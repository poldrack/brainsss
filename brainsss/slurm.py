# refactor of slurm utils

# pyright: reportMissingImports=false

from preprocess_utils import dict_to_args_list
import subprocess
import logging
import time
import os
import sys
sys.path.insert(0, "../brainsss")
sys.path.insert(0, "../brainsss/scripts")
from logging_utils import remove_existing_file_handlers  # noqa

# set up module level logging
logger = logging.getLogger('SlurmBatchJob')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('|%(asctime)s|%(name)s|%(levelname)s\n%(message)s\n')
ch.setFormatter(formatter)
logger.addHandler(ch)


class SlurmBatchJob:
    def __init__(self, jobname: str, script: str,
                 user_args: dict = None, verbose: bool = False,
                 logfile: str = None, local=False,
                **kwargs):
        """
        Class to define and run a slurm job

        Parameters
        ----------
        jobname : str
            name of the job
        script : str
            path to the script to run
        user_args : dict
            dictionary of arguments to pass to the script
        verbose : bool
            enable verbose logging
        logfile : str
            path to logfile (if not specified, logs to stdout only)
        local : bool
            run job locally instead of on slurm
        kwargs : dict
            additional arguments to pass to the sbatch command

        """
        self.jobname = jobname
        self.script = script
        self.job_id = None
        self.output = None
        self.verbose = verbose
        self.logfile = None
        self.logdir = None
        self.local = local
        self.local_response = None
        self.local_run = False
        self.sbatch_run = False

        # first remove any outside file logger
        self.saved_handlers = remove_existing_file_handlers()

        if logfile is not None:
            self.logfile = logfile
        elif 'logfile' in user_args:
            self.logfile = user_args['logfile']

        if self.logfile is not None:
            self.logdir = os.path.dirname(os.path.realpath(self.logfile))
            if not os.path.exists(self.logdir):
                os.makedirs(self.logdir)
            fh = logging.FileHandler(self.logfile)
            formatter = logging.Formatter(
                '|%(asctime)s|%(name)s|%(levelname)s\n%(message)s\n')
            fh.setFormatter(formatter)
            logger.addHandler(fh)
            logger.debug(f'log dir: {self.logdir}')
        else:
            logger.info('No logfile specified - logging to stdout only')

        if self.verbose:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

        logger.info('Setting up SlurmBatchJob')
        # check args
        assert os.path.exists(self.script)

        self.default_args = {
            'nice': False,
            'time_hours': 1,
            'module_string': '',
            'node_cmd': '',
            'cores': 1,
            'partition': 'normal',
        }

        self.setup_args(user_args, kwargs)
        logger.info(f'args: {self.args}')

        self.command = (
            f"{self.args['module_string']}"
            f"python3 {self.script} {' '.join(dict_to_args_list(self.args))}"
        )
        logger.debug(f'command: {self.command}')

        self.sbatch_command = (
            f"sbatch -J {jobname} -o {self.logfile} --wrap='{self.command}' "
            f"--nice={self.args['nice']} {self.args['node_cmd']} --open-mode=append "
            f"--cpus-per-task={self.args['cores']} --partition={self.args['partition']} "
            f"-e {self.logfile} "
            f"-t {self.args['time_hours']}:00:00"
        )
        logger.debug(f'sbatch_command: {self.sbatch_command}')

    def setup_args(self, user_args, kwargs):
        # extend default args with user args and kwargs
        self.args = self.default_args
        if isinstance(user_args, dict):
            self.args = self.default_args
            self.args.update(user_args)
        elif user_args is not None:
            raise TypeError('args must be dict or None')

        self.args.update(kwargs)

    def run(self):
        if self.local:
            self.run_local()

        sbatch_response = subprocess.getoutput(self.sbatch_command)
        setattr(self, 'job_id', sbatch_response.split(" ")[-1].strip())
        logger.debug(f'job_id: {self.job_id}')
        if self.job_id is not None:
            self.sbatch_run = True
        setattr(self, 'sbatch_response', sbatch_response)
        logger.debug(f'sbatch_response: {self.sbatch_response}')

    def run_local(self):
        """run without slurm"""
        logger.info(f'Running job locally: {self.jobname}')
        setattr(self, 'job_id', None)
        logger.info(f'command: {self.command}')
        response = subprocess.run(self.command, shell=True)
        setattr(self, 'local_response', response)
        logger.info(f'response: {response}')
        if response is not None:
            setattr(self, 'local_run', True)

    def wait(self, wait_time=5):
        if self.local:
            logger.warning('Cannot wait for local job - returning output from local job')
            return(self.local_response)

        if not self.sbatch_run:
            logging.warning('Cannot wait for job - job not run')

        while True:
            status = self.status()
            if status is not None and status not in ['PENDING', 'RUNNING', 'CONFIGURING']:
                status = self.status(return_full_output=True)
                logger.info(f'Job {self.job_id} finished with status: {status}\n\n')
                logger.info(f'opening log_file: {self.logfile}')
                try:
                    with open(self.logfile, "r") as f:
                        output = f.read()
                except FileNotFoundError:
                    logger.warning(f'Could not find log file: {self.logfile}')
                    output = None
                return output
            else:
                time.sleep(wait_time)

    def status(self, return_full_output=False):
        if self.local:
            if self.local_response is None:
                logging.warning('Cannot get status of local job - no response')
            else:
                return('COMPLETED')

        if not self.sbatch_run:
            logging.warning('Cannot get status of job - job not run')
            return None

        temp = subprocess.getoutput(
            f"sacct -n -P -j {self.job_id} --noconvert --format=State,Elapsed,MaxRSS,NCPUS,JobName"
        )

        status = None if temp == "" else temp.split("\n")[0].split("|")[0].upper()

        return temp if return_full_output else status


if __name__ == "__main__":
    argdict = {'time_hours': 1}
    sbatch = SlurmBatchJob('test', 'dummy_script.py',
        argdict, verbose=True, logfile='test.log')
    print(sbatch.sbatch_command)
    sbatch.run()
    print(sbatch.sbatch_response)
    print(sbatch.job_id)
    print(sbatch.status())
    print(sbatch.wait())
