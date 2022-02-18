#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct  8 14:53:40 2019
@author: au571533, Roberta Rocca

"""

import pandas as pd
from pliers.stimuli import ComplexTextStim
from pliers.extractors import PredefinedDictionaryExtractor, merge_results
from matplotlib import pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import seaborn as sns
from numpy import repeat, array

###### READ IN THE BINDER AND RUN PCA ON VALENCE DIMENSIONS #######
# Plug in working directory and path to Binder database
wd = '/Users/au571533/Dropbox/DeixisSurvey2/AdvCogNeuro_2019'
path_to_binder = '/Users/au571533/Dropbox/DeixisSurvey2/prolific2_material/WordSet1_Ratings.xlsx'

# Import the binder
binder_data = pd.read_excel(path_to_binder)

# Run PCA with two components (we will only use one here)
pca = PCA(n_components=2) # define structure
features = ['Pleasant', 'Unpleasant', 'Happy', 'Sad']
x = StandardScaler().fit_transform(binder_data[features]) # Rescale
pca_model = pca.fit_transform(x) # apply
binder_data[['PC1', 'PC2']] = pd.DataFrame(data = pca_model, columns = ['PC1', 'PC2'])

# Check variance explained by each PC
pca.explained_variance_ratio_

###### FIND SENTIMENT SCORES FROM WARRINER AND APPEND #######
# Find sentiment scores in Warriner database using pliers
val_ext = PredefinedDictionaryExtractor(variables = ['affect/V.Mean.Sum'])
word_stim = ComplexTextStim(text = ' '.join(binder_data['Word']), unit = 'word')
result = val_ext.transform(stim = word_stim)
result_df = merge_results(result, extractor_names = 'drop')
result_df.stim_name = result_df.stim_name.str[5:-1]

###### CREATE WORD LIST #####################
# Merge with original database
binder_data = binder_data.merge(result_df.iloc[:,[7,9]], 
                                left_on='Word', right_on='stim_name', how = 'outer')
binder_data = binder_data[binder_data['affect_V.Mean.Sum'].isna() == False]


# Valence split based on PC1 and validated on Warriner
binder_data = binder_data.sort_values('PC1').reset_index()
pos_word_df = binder_data[binder_data['affect_V.Mean.Sum'] > 6].head(n = 120)
neg_word_df = binder_data[binder_data['affect_V.Mean.Sum'] < 5].tail(n = 120)
neu_word_df = binder_data[(binder_data['affect_V.Mean.Sum'] < 6) & 
                            (binder_data['affect_V.Mean.Sum'] > 5)].head(n = 120)

# Shuffle and subset
pos_word_df = pos_word_df.sample(frac = 1).reset_index(drop=True)
neg_word_df = neg_word_df.sample(frac = 1).reset_index(drop=True)
neu_word_df = neu_word_df.sample(frac = 1).reset_index(drop=True)
pos_word_df = pos_word_df[['Word','PC1', 'affect_V.Mean.Sum']]
neg_word_df = neg_word_df[['Word','PC1', 'affect_V.Mean.Sum']]
neu_word_df = neu_word_df[['Word','PC1', 'affect_V.Mean.Sum']]

# Create sessions with 60 words each and append to common database
all_words_df = pd.DataFrame()
for c in range(6):
    
    session_df = pd.concat([pos_word_df.loc[range(20 * c, 20 * c + 20)], 
                            neg_word_df.loc[range(20 * c, 20 * c + 20)],
                            neu_word_df.loc[range(20 * c, 20 * c + 20)]], axis = 0) 
    session_df['label'] = repeat(['pos', 'neg', 'neu'], repeats = 20)
    session_df['session'] = c + 1 
    all_words_df = all_words_df.append(session_df)

# Save format
all_words_df.columns = ['word', 'score_pc', 'score_warriner', 'label', 'session']
all_words_df.to_csv(wd + '/wordlist.txt', sep = '\t') 

######  SUMMARIZE VALENCE DISTRIBUTION BY SESSION #####################
# Check valence by session (plot)
colors = ['darkblue','darkred','orange']
titles = ['positive_valence', 'negative_valence', 'neutral_valence']
c = 0 # Index for loop

# Loop and plot
for valence in ['pos','neg','neu']:
    session_df = all_words_df[all_words_df.label == valence]
    g = sns.FacetGrid(session_df, col = 'session', col_wrap = 3)
    g = g.map(plt.hist, "score_pc", color = colors[c])
    g.fig.suptitle(titles[c])
    plt.subplots_adjust(top=0.9)
    c = c + 1
del session_df
  
# Now extract summary stats for each session and valence category
all_words_summary = pd.pivot_table(all_words_df, aggfunc = ['mean', 'median', 'max', 'min'], index = ['label','session'], values = ['score_pc', 'score_warriner'])
all_words_summary = all_words_summary.reset_index()
all_words_summary.columns = list(['_'.join(col).strip() for col in all_words_summary.columns.values])
all_words_summary.columns.values[[0,1]] = array(['session','label'])

# Store summary info in tsv file
all_words_summary.to_csv(wd + 'summary_info_sessions.txt', sep = '\t') 

