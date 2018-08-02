from __future__ import division, print_function

import numpy as np

import energyflow as ef
from energyflow.archs import EFN
from energyflow.datasets import qg_jets
from energyflow.utils import data_split, to_categorical

# attempt to import sklearn
try:
    from sklearn.metrics import roc_auc_score, roc_curve
except:
    print('please install scikit-learn in order to make ROC curves')
    roc_curve = False

# attempt to import matplotlib
try:
    import matplotlib.pyplot as plt
except:
    print('please install matploltib in order to make plots')
    plt = False


################################### SETTINGS ###################################

# data controls
num_data = 100000
val_frac, test_frac = 0.1, 0.15

# network architecture parameters
ppm_sizes = (100, 100)
dense_sizes = (100, 100)

# network training parameters
num_epoch = 5
batch_size = 100

################################################################################

# load data
X, y = qg_jets.load(num_data=num_data)

# convert labels to categorical
Y = to_categorical(y, num_classes=2)

print()
print('Loaded quark and gluon jets')

# ignore pid information
X = X[:,:,:3]

# preprocess by centering jets and normalizing pts
for x in X:
    mask = x[:,0] > 0
    yphi_avg = np.average(x[mask,1:3], weights=x[mask,0], axis=0)
    x[mask,1:3] -= yphi_avg
    x[mask,0] /= x[:,0].sum()

print('Finished preprocessing')

# do train/val/test split 
(z_train, z_val, z_test, 
 p_train, p_val, p_test,
 Y_train, Y_val, Y_test) = data_split(X[:,:,0], X[:,:,1:], Y, 
                                      val=val_frac, test=test_frac)

print('Done train/val/test split')
print('Model summary:')

# build architecture
model = EFN(input_dim=2, ppm_sizes=ppm_sizes, dense_sizes=dense_sizes)

# train model
model.fit([z_train, p_train], Y_train,
          epochs=num_epoch,
          batch_size=batch_size,
          validation_data=([z_val, p_val], Y_val),
          verbose=1)

# get ROC curve
preds = model.predict([z_test, p_test], batch_size=1000)

if roc_curve:
    efn_fp, efn_tp, threshs = roc_curve(Y_test[:,1], preds[:,1])
    auc = roc_auc_score(Y_test[:,1], preds[:,1])
    print()
    print('EFN AUC:', auc)
    print()

    if plt:

        # get multiplicity and mass for comparison
        masses = np.asarray([np.sqrt(ef.mass2(ef.p4s_from_ptyphis(x).sum(axis=0))) for x in X])
        mults = np.asarray([np.count_nonzero(x[:,0]) for x in X])
        
        mass_fp, mass_tp, threshs = roc_curve(Y[:,1], -masses)
        mult_fp, mult_tp, threshs = roc_curve(Y[:,1], -mults)

        plt.rcParams['figure.figsize'] = (4,4)
        plt.rcParams['font.family'] = 'serif'
        plt.rcParams['figure.autolayout'] = True

        plt.plot(efn_tp, 1-efn_fp, '-', color='black', label='EFN')
        plt.plot(mass_tp, 1-mass_fp, '-', color='blue', label='Jet Mass')
        plt.plot(mult_tp, 1-mult_fp, '-', color='red', label='Multiplicity')

        plt.xlabel('Quark Jet Efficiency')
        plt.ylabel('Gluon Jet Rejection')

        plt.xlim(0, 1)
        plt.ylim(0, 1)

        plt.legend(loc='lower left', frameon=False)
        plt.show()
