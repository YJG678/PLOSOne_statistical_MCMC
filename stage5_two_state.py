#!/usr/bin/env python3
"""Experiment A: exact Markov-binomial two-state metastability study."""
from __future__ import annotations
import csv, json, math
from pathlib import Path
import numpy as np
from scipy.stats import beta, binom

OUT=Path("stage5_outputs/experiment_A"); OUT.mkdir(parents=True,exist_ok=True)
SEED=310000001; rng=np.random.default_rng(SEED)
n=200; reps=5000; grid=np.logspace(-2,2,13); ps=[.5,.1,.01]; Ls=[4,16,64]

def markov_binomial_joint(p,eps):
    """Exact joint law of S_n=sum(X_0,...,X_{n-1}) and X_n, given X_0=0."""
    q=np.zeros((n+1,2)); q[0,0]=1.
    P=np.array([[1-eps*p,eps*p],[eps*(1-p),1-eps*(1-p)]])
    for t in range(n):
        nq=np.zeros_like(q)
        for k in range(t+1):
            for state in (0,1):
                next_k=k+state
                nq[next_k,:]+=q[k,state]*P[state,:]
        q=nq
    q[q<0]=0
    return q/q.sum()

def cp_upper(k,L,eta=.05): return 1 if k==L else float(beta.ppf(1-eta,k+1,L-k))

rows=[]
for p in ps:
 for ne in grid:
  eps=float(ne/n); joint=markov_binomial_joint(p,eps); pmf=joint.sum(axis=1); kval=np.arange(n+1); vals=kval/n
  mean=float(pmf@vals); var=float(pmf@(vals-mean)**2); bias=mean-p; mse=var+bias*bias
  z=(1-eps*p)**n; zero_disp_theory=z # all chains zero event becomes z^L below
  iid_pmf=binom.pmf(kval,n,p); iid_vals=vals
  for L in Ls:
   sticky_joint_idx=rng.choice(2*(n+1),size=(reps,L),p=joint.ravel())
   sticky_idx=sticky_joint_idx//2
   sticky_terminal=sticky_joint_idx%2
   iid_idx=rng.binomial(n,p,size=(reps,L))
   s=sticky_idx/n; q=iid_idx/n
   sdisp=s.var(axis=1,ddof=1); qdisp=q.var(axis=1,ddof=1)
   naive_sticky=sdisp<qdisp # tie goes to reliable iid
   true_iid_mse=p*(1-p)/n
   inferior_sticky=mse>true_iid_mse
   naive_error=np.mean(naive_sticky) if inferior_sticky else np.mean(~naive_sticky)
   failures=((sticky_idx==0)&(sticky_terminal==0)).sum(axis=1)
   gate_pass=np.array([cp_upper(int(k),L)<=.1 for k in failures])
   gated_sticky=gate_pass & naive_sticky
   gated_error=np.mean(gated_sticky) if inferior_sticky else np.mean(~gated_sticky)
   obs_zero=np.mean(np.ptp(s,axis=1)==0)
   # exact zero dispersion has more possibilities, but metastable false-precision event is all-zero.
   obs_all_zero=np.mean(np.all((sticky_idx==0)&(sticky_terminal==0),axis=1)); th_all_zero=z**L
   se=math.sqrt(th_all_zero*(1-th_all_zero)/reps)
   rows.append(dict(p=p,n=n,n_epsilon=ne,epsilon=eps,L=L,repetitions=reps,
    exact_bias=bias,exact_D=n*var,exact_R=n*mse,exact_mse=mse,iid_mse=true_iid_mse,
    theorem_all_zero_probability=th_all_zero,mc_all_zero_probability=obs_all_zero,
    mc_all_zero_se=se,mc_any_zero_dispersion=obs_zero,transition_screen_pass_frequency=gate_pass.mean(),
    naive_selection_error=naive_error,gated_selection_error=gated_error,
    sticky_is_inferior=inferior_sticky))

with (OUT/"two_state_results.csv").open("w",newline="") as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
maxz=max(abs(r["mc_all_zero_probability"]-r["theorem_all_zero_probability"])/(r["mc_all_zero_se"] or 1/reps) for r in rows)
prevent=[r for r in rows if r["naive_selection_error"]>.1 and r["gated_selection_error"]<r["naive_selection_error"]-.05]
summary={"experiment":"A","seed":SEED,"configurations":len(rows),"meta_repetitions_per_configuration":reps,
 "maximum_standardized_theorem_mc_error":maxz,"settings_demonstrating_prevented_false_selection":len(prevent),
 "status":"PASS" if maxz<5 and prevent else "FAIL"}
(OUT/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
print(json.dumps(summary,indent=2))
