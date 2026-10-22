#!/usr/bin/env python3
"""Exact two-state certification-power benchmark with independent datasets."""
from __future__ import annotations
import csv,json,math
from pathlib import Path
import numpy as np
from scipy.stats import beta

OUT=Path("stage7_outputs/certification"); OUT.mkdir(parents=True,exist_ok=True)
SEED=330000001; rng=np.random.default_rng(SEED)
p=.5; n=20; m=551; delta=.015; meta=2000; eps_grid=[.001,.01,.05,.10,.25,1.0]
radius=math.sqrt(2*math.log(1/delta)/m)

def pmf(eps):
 a=np.zeros(n+1); b=np.zeros(n+1); a[0]=1
 for t in range(1,n):
  na=np.zeros_like(a); nb=np.zeros_like(b)
  na[:t]=a[:t]*(1-eps*p)+b[:t]*eps*(1-p)
  nb[1:t+1]=a[:t]*eps*p+b[:t]*(1-eps*(1-p))
  a,b=na,nb
 q=a+b; return q/q.sum()
def ci(k,N):
 return (0 if k==0 else float(beta.ppf(.025,k,N-k+1)),1 if k==N else float(beta.ppf(.975,k+1,N-k)))

rows=[]
for eps in eps_grid:
 q=pmf(eps); kval=np.arange(n+1)
 sticky_mse=float(q@((kval/n-p)**2)); iid_mse=p*(1-p)/n; gap=sticky_mse-iid_mse
 certified=0
 for _ in range(meta):
  bad=rng.choice(n+1,size=m,p=q)/n
  good=rng.binomial(n,p,size=m)/n
  W=(bad-p)**2-(good-p)**2
  certified += W.mean()-radius>0
 lo,hi=ci(certified,meta)
 rows.append(dict(epsilon=eps,p=p,horizon=n,certification_units=m,true_bad_mse=sticky_mse,true_good_mse=iid_mse,true_improvement=gap,hoeffding_radius=radius,meta_repetitions=meta,certifications=certified,certification_power=certified/meta,ci95_lower=lo,ci95_upper=hi))

# Null calibration: two iid candidates, disjoint synthetic certification datasets.
false=0
for _ in range(meta):
 a=rng.binomial(n,p,size=m)/n; b=rng.binomial(n,p,size=m)/n
 W=(a-p)**2-(b-p)**2
 false += W.mean()-radius>0
null_ci=ci(false,meta)

with (OUT/"certification_power.csv").open("w",newline="") as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
summary={"experiment":"C_exact_certification","seed":SEED,"p":p,"horizon":n,"certification_units":m,"delta":delta,"hoeffding_radius":radius,"meta_repetitions_per_setting":meta,"primary_epsilon":.001,"primary_power":rows[0]["certification_power"],"primary_power_ci95":[rows[0]["ci95_lower"],rows[0]["ci95_upper"]],"null_false_certifications":int(false),"null_false_certification_rate":float(false/meta),"null_ci95":null_ci,"status":"PASS" if rows[0]["certification_power"]>=.8 and false/meta<=delta else "FAIL"}
(OUT/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
print(json.dumps(summary,indent=2))
