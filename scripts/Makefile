BASEDIR = /data/brainsss
QUEUE = trc #normal
BASEDIR = /scratch/users/russpold/brainsss
PROCESS =  "--highpass --fictrac_qc --STB --bleaching_qc" #"--motion_correction func --type_of_transform Rigid"


clean:
	-rm -rf  $(BASEDIR)/logs/* $(basedir)/processed/fly_*/func_*/logs $(BASEDIR)/master_2P.xlsx

clean-all:
	-rm -rf $(BASEDIR)/processed/* $(BASEDIR)/logs/* $(BASEDIR)/master_2P.xlsx
test-build-local:
	bash preprocess.sh --local -b $(BASEDIR) -v --no_require_settings --build --import_date 20220329 

test-build-local-sherlock:
	bash preprocess.sh --local -b $(BASEDIR) -v --no_require_settings --build --import_date 20220329 --import_dir /oak/stanford/groups/trc/data/Brezovec/2P_Imaging/imports  --fly_dirs fly_2

test-proc-local:
	python preprocess.py -b $(BASEDIR) -v --no_require_settings --$(PROCESS) --process $(BASEDIR)/processed/fly_001 --local

test-both-local:
	python preprocess.py -b $(BASEDIR) --build --import_date 20220329 -v --no_require_settings --$(PROCESS) --local

test-build-slurm:
	sbatch preprocess.sh --partition=$(QUEUE) -b $(BASEDIR) -v --no_require_settings --build --import_date 20220329

test-proc-slurm:
	sbatch preprocess.sh --partition=$(QUEUE) -b $(BASEDIR) -v --no_require_settings --$(PROCESS) --process $(BASEDIR)/processed/fly_001

test-both-slurm:
	sbatch preprocess.sh --partition=$(QUEUE) -b $(BASEDIR) --import_date 20220329  -v --no_require_settings --$(PROCESS) --build 

test-build-slurm-sherlock:
	sbatch preprocess.sh --partition=$(QUEUE) -b $(BASEDIR) --import_date 20220329 --fly_dirs fly_2 --func_dirs func_0 -v --no_require_settings --build-only --build --import_dir /oak/stanford/groups/trc/data/Brezovec/2P_Imaging/imports

test-both-slurm-sherlock:
	sbatch preprocess.sh --cores 8 --partition=$(QUEUE) -b $(BASEDIR) --import_date 20220329 --fly_dirs fly_2 --func_dirs func_0 -v --no_require_settings $(PROCESS) --build --import_dir /oak/stanford/groups/trc/data/Brezovec/2P_Imaging/imports

test-proc-slurm-sherlock:
	sbatch preprocess.sh --cores 8 --partition=$(QUEUE) -b $(BASEDIR) -v --no_require_settings --process $(BASEDIR)/processed/fly_001 $(PROCESS) --func_dirs func_0
