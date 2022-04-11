from brainsss.visual import load_photodiode, get_stimulus_metadata,\
    extract_stim_times_from_pd
from brainsss.fictrac import smooth_and_interp_fictrac, load_fictrac
import numpy as np
import matplotlib.pyplot as plt
import os
import json
import sys
import argparse


def parse_args(input):
    parser = argparse.ArgumentParser(description='process stimulus triggered behavior')
    parser.add_argument('-d', '--dir', type=str, 
        help='base directory for imaging session', required=True)
    parser.add_argument('--fps', type=float, default=100, help='frame rate of fictrac camera')
    # TODO: What is this? not clear from smooth_and_interp_fictrac
    parser.add_argument('--resolution', default=10, type=float, help='resolution of fictrac data')
    args = parser.parse_args(input)
    return(args)


def plot_avg_trace(fictrac, starts_angle_0, starts_angle_180, vision_path, printlog=None):
    pre_window = 200 # in units of 10ms
    post_window = 300

    traces = []
    for i in range(len(starts_angle_0)):
        trace = fictrac['Z'][starts_angle_0[i]-pre_window:starts_angle_0[i]+post_window]
        if len(trace) == pre_window + post_window: # this handles fictrac that crashed or was aborted or some bullshit
            traces.append(trace)
    mean_trace_0 = np.mean(np.asarray(traces),axis=0)

    traces = []
    for i in range(len(starts_angle_180)):
        trace = fictrac['Z'][starts_angle_180[i]-pre_window:starts_angle_180[i]+post_window]
        if len(trace) == pre_window + post_window: # this handles fictrac that crashed or was aborted or some bullshit
            traces.append(trace)
    mean_trace_180 = np.mean(np.asarray(traces),axis=0)

    plt.figure(figsize=(10,10))
    xs = np.arange(-pre_window,post_window)*10
    plt.plot(xs, mean_trace_0,color='r',linewidth=5)
    plt.plot(xs, mean_trace_180,color='cyan',linewidth=5)
    plt.axvline(0,color='grey',lw=3,linestyle='--') # stim appears
    plt.axvline(1000,color='k',lw=3,linestyle='--') # stim moves
    plt.axvline(1500,color='grey',lw=3,linestyle='--') # grey
    plt.ylim(-50,50)
    plt.xlabel('Time, ms')
    plt.ylabel('Angular Velocity')

    name = 'stim_triggered_turning.png'
    fname = os.path.join(vision_path, name)
    plt.savefig(fname,dpi=100,bbox_inches='tight')
    printlog(F"saved {fname}")



if __name__ == '__main__':
    args = parse_args(sys.argv[1:])
    
    #logfile = args['logfile']
    # func_path = args['func_path']
    # printlog = getattr(brainsss.Printlog(logfile=logfile), 'print_to_log')


    ###########################
    ### PREP VISUAL STIMULI ###
    ###########################

    vision_path = os.path.join(args.dir, 'visual')

    ### Load Photodiode ###
    t, ft_triggers, pd1, pd2 = load_photodiode(vision_path)
    stimulus_start_times = extract_stim_times_from_pd(pd2, t)

    ### Get Metadata ###
    stim_ids, angles = get_stimulus_metadata(vision_path)
    #printlog(F"Found {len(stim_ids)} presented stimuli.")

    # *100 puts in units of 10ms, which will match fictrac
    starts_angle_0 = [int(stimulus_start_times[i]*100) for i in range(len(stimulus_start_times)) if angles[i] == 0]
    starts_angle_180 = [int(stimulus_start_times[i]*100) for i in range(len(stimulus_start_times)) if angles[i] == 180]
    #printlog(F"starts_angle_0: {len(starts_angle_0)}. starts_angle_180: {len(starts_angle_180)}")

    ####################
    ### PREP FICTRAC ###
    ####################

    fictrac_path = os.path.join(args.dir, 'fictrac')
    fictrac_raw = load_fictrac(fictrac_path)

    expt_len = fictrac_raw.shape[0]/args.fps*1000
    behaviors = ['dRotLabY', 'dRotLabZ']
    fictrac = {}
    for behavior in behaviors:
        if behavior == 'dRotLabY': short = 'Y'
        elif behavior == 'dRotLabZ': short = 'Z'
        fictrac[short] = smooth_and_interp_fictrac(fictrac_raw, args.fps, args.resolution, expt_len, behavior)
    xnew = np.arange(0,expt_len,args.resolution)

    ##################
    ### MAKE PLOTS ###
    ##################
    plot_avg_trace(fictrac, starts_angle_0, starts_angle_180, vision_path)

