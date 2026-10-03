#!/usr/bin/python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def selectGroup():
    print()
    groups = ['Group1', 'Group2', 'Group3']
    for i, name in enumerate(groups, 1):
        print(f"\t{i}. {name}")
    selection = input('\nPlease enter the NUMBER of the Group you would like to load: ').rstrip()
    selected_group = ''
    
    if selection.isdigit():
        selection = int(selection)
        if 1 <= selection <= len(groups):
            selected_group = groups[selection - 1]
            print('\nYou selected ' + selected_group)
        else:
            print(str(selection) + ' is not a valid selection.')
    else:
        print('Please select a number.')
    return selected_group

def selectExcelSheet(fname):
    xls = pd.ExcelFile(fname)
    print("Available sheets in " + fname  + ":")
    print()
    for i, name in enumerate(xls.sheet_names, 1):
        print(f"\t{i}. {name}")
    
    selection = input('\nPlease enter the NUMBER of the data you would like to load: ').rstrip()
    
    if selection.isdigit():
        selection = int(selection)
        if 1 <= selection <= len(xls.sheet_names):
            selected_sheet = xls.sheet_names[selection - 1]
            print('\nYou selected ' + selected_sheet)
            df = xls.parse(selected_sheet)
        else:
            print(str(selection) + ' is not a valid selection.')
    else:
        print('Please select a number.')
        return
    return df

def contraLegs(legs):
    # set up contralateral leg relationships
    contra_legs = {}
    for i in range(0,len(legs),2):
        contra_legs[legs[i]] = legs[i+1]
        contra_legs[legs[i+1]] = legs[i]
    return [contra_legs[leg] for leg in legs]

def stepTimingToKinematics(df, legs = ['Left','Right'], states = ['DOWN','UP']):
    # make a new dataframe of step kinematics from this step timing dataframe
    contra_legs = contraLegs(legs)
    
    stepdata = {}
    for leg in legs:
        for state in states:
            k = leg + ' ' + state
            stepdata[k] = df[k].dropna().to_numpy()
    
    data = {}
    data['leg id'] = []
    data['step time'] = []
    data['stride duration']= []
    data['stance duration'] = []
    data['duty factor'] = []
    data['contralateral offset'] = []
    data['contralateral phase offset'] = []
    
    for i, leg in enumerate(legs):
    
        downs = stepdata[leg + ' ' + states[0]]
        ups = stepdata[leg + ' ' + states[1]]
        contra_downs = stepdata[contra_legs[i] + ' ' + states[0]]
    
        # for each leg make nan vectors for with same length as down steps
        leg_ids = [leg for x in downs]
        stride_durations = np.full(len(downs), np.nan)
        stance_durations = np.full(len(downs), np.nan)
        duty_factors = np.full(len(downs), np.nan)
        offsets = np.full(len(downs), np.nan)
        phase_offsets = np.full(len(downs), np.nan)
    
        # fill these vectors up for each down step
        for j, down in enumerate(downs):
            
            # find first value in comparison factor that is greater than this value
            next_up = np.where(ups > down)[0]
            if len(next_up) > 0:
                stance_durations[j] = ups[next_up][0] - down
                
            next_down = np.where(downs > down)[0]
            if len(next_down) > 0:
                stride_durations[j] = downs[next_down][0] - down
    
            next_contra = np.where(contra_downs > down)[0]
            if len(next_contra) > 0:
                offsets[j] = contra_downs[next_contra][0] - down
    
            if stance_durations[j] and stride_durations[j]:
                duty_factors[j] = stance_durations[j] / stride_durations[j]
    
            if offsets[j] and stride_durations[j]:
                phase_offsets[j] = offsets[j] / stride_durations[j]
    
        # add data for this leg to the dictionary
        data['leg id'].extend(leg_ids)
        data['step time'].extend(downs)
        data['stride duration'].extend(stride_durations)
        data['stance duration'].extend(stance_durations)
        data['duty factor'].extend(duty_factors)
        data['contralateral offset'].extend(offsets)
        data['contralateral phase offset'].extend(phase_offsets)
    return pd.DataFrame(data).dropna()

def kinematicsPlot(kinematics, color='salmon'):
    # Plots from ONE set of kinematics data:
    # Show stride duration, duty factor, contralateral phase offset
    plot_cols = ['stride duration', 'duty factor', 'contralateral phase offset']
    fig, axes = plt.subplots(1, len(plot_cols), figsize=(3*len(plot_cols), 3))
    for i, col in enumerate(plot_cols):
        ax = axes[i]
        sns.boxplot(data=kinematics, y=col, ax=ax, showfliers=False, color=color, width=0.5)
        sns.stripplot(data=kinematics, y=col, ax=ax, color='k')
        if 'duty' in col or 'phase' in col:
            ax.set_ylim([0.3,0.7])
        elif 'duration' in col:
            ax.set_ylim([0.4,1.5])
            ax.set_ylabel(col + ' (sec)')
    plt.tight_layout()
    plt.show()

def loadGroupData(fname, group):
    # Load all available data for a particular group 
    #     into a dictionary of dataframes, keyed by treatment
    
    xls = pd.ExcelFile(fname)
    sheets = [x for x in xls.sheet_names if group in x]
    treatments = [x.split(' - ')[1] for x in sheets]
    
    kinematics_dfs = {} # keyed by treatment
    
    for i, sheet in enumerate(sheets):
        df = xls.parse(sheet)
        kinematics_dfs[treatments[i]] = stepTimingToKinematics(df)
    
    return kinematics_dfs

def gaitColors():
    gait_colors = {}
    gait_colors['slow walk'] = '#3123ad'
    gait_colors['fast walk'] = '#26ad2b'
    gait_colors['slow run'] = '#f59300'
    gait_colors['fast run'] = '#c90502'
    return gait_colors

def compareKinematics(kinematics_dfs):
    # For a dictionary of kinematics dataframes
    #     compare kinematics on plots: stride duration, duty factor, contralateral phase offset
    cols = ['stride duration','duty factor','contralateral phase offset']
    fig, axes = plt.subplots(1,3, figsize=(12,4))
    gait_colors = gaitColors()
    
    for i, col in enumerate(cols):
        plot_data = []
        ax=axes[i]
        xlabs = []
        colors = []
        for treatment in kinematics_dfs.keys():
            plot_data.append(kinematics_dfs[treatment][col].values)
            xlabs.append(treatment)
            colors.append(gait_colors[treatment])
        sns.boxplot(plot_data, ax=ax, showfliers=False, palette=colors)
        sns.stripplot(plot_data, ax=ax, color='k')
        ax.set_ylabel(col, fontsize=14)
        xlabs = [x.replace(' ','\n') for x in xlabs]
        ax.set_xticks([0,1,2], xlabs, fontsize=14)
        if 'duration' in col:
            ax.set_ylabel(col + ' (sec)', fontsize=14)
    
    plt.tight_layout()
    plt.show()

def dutyContraScatter(kinematics_dfs, kde=False):
    f,ax = plt.subplots(1,1,figsize=(6,6))
    gait_colors = gaitColors()
    colormap_name = 'Grays'
    cmap = plt.get_cmap(colormap_name) 
    ax_background = cmap(0)  
    
    i = 0.15
    for treatment in kinematics_dfs.keys():
        phase_offsets = kinematics_dfs[treatment]['contralateral phase offset']
        duty_factors = kinematics_dfs[treatment]['duty factor']
        single_side_proportions = [1-x if x > 0.5 else x for x in phase_offsets]
        if kde:
            ax = sns.kdeplot(ax=ax, x=single_side_proportions, y=duty_factors, 
                             fill=True, cmap=colormap_name, thresh=0, levels=50, common_norm=False, alpha=0.5,
                             warn_singular=False)
        ax.scatter(single_side_proportions, duty_factors, s=15, c=gait_colors[treatment])
        ax.plot(0.05,i,'o',markersize=5,color=gait_colors[treatment])
        ax.text(0.1, i-0.01, treatment)
        i = i-0.05
         
    ax.set_xlabel('Contralateral Phase Offset', fontsize=14)
    ax.set_ylabel('Duty Factor', fontsize=14)
    ax.set_aspect('equal', adjustable='box')
    ax.set_xlim([0, 0.55])
    ax.set_ylim([0, 1])
    ax.set_facecolor(ax_background)
    
    plt.show()