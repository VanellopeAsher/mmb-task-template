"""Author-only deterministic geometric models from MIT-licensed MOFUN fixture.
Not relaxed structures, experimental observations or the Islamov simulation files.
"""
from pathlib import Path
from collections import Counter
import hashlib, json, tempfile
import numpy as np
from ase.io import read, write
from scipy.spatial.distance import cdist
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components

ROOT = Path(__file__).resolve().parents[2]
def components(x, box, cutoff):
    d=x[:,None,:]-x[None,:,:];d-=np.round(d/box)*box
    graph=np.linalg.norm(d,axis=2)<cutoff
    _, labels=connected_components(csr_matrix(graph))
    return [np.flatnonzero(labels==i) for i in np.unique(labels)]
def centroid(x, box):
    d=x-x[0];d-=np.round(d/box)*box
    return (x[0]+np.mean(d,axis=0))%box
def main():
    source=ROOT/'authoring/provenance/uio66_mofun.cif'
    atoms=read(source).repeat((3,3,3));box=atoms.cell.lengths();x=atoms.positions%box
    symbols=np.array(atoms.get_chemical_symbols());zi=np.where(symbols=='Zr')[0];ci=np.where(symbols=='C')[0]
    zg=components(x[zi],box,4.5);cg=components(x[ci],box,1.8)
    z=np.array([centroid(x[zi[g]],box) for g in zg]);c=np.array([centroid(x[ci[g]],box) for g in cg])
    if len(z)!=108 or len(c)!=648: raise ValueError('Unexpected reference')
    delta=z[None,:,:]-c[:,None,:];delta-=np.round(delta/box)*box
    ends=np.argsort(np.linalg.norm(delta,axis=2),axis=1)[:,:2]
    # Atom membership independently reconstructed with dense distances.
    carbon_owner={int(i):k for k,g in enumerate(cg) for i in ci[g]}
    owner=[]
    for i,q in enumerate(x):
        dc=x[ci]-q;dc-=np.round(dc/box)*box;dist=np.linalg.norm(dc,axis=1)
        if symbols[i]=='C' or (symbols[i] in ['O','H'] and dist.min()<1.7):
            owner.append(('l',carbon_owner[int(ci[np.argmin(dist)])]))
        else:
            dz=z-q;dz-=np.round(dz/box)*box
            owner.append(('c',int(np.argmin(np.linalg.norm(dz,axis=1)))))
    rng=np.random.default_rng(20261113)
    def random_sites(n,k): return set(map(int,rng.choice(n,k,replace=False)))
    motif=np.mod(z/20.7004,1);motif[np.isclose(motif,1)]=0
    ordered_cluster=set(np.flatnonzero(np.all(np.isclose(motif,0,atol=1e-4),axis=1)).tolist())
    displacement=z[ends[:,1]]-z[ends[:,0]];displacement-=np.round(displacement/box)*box
    ordered_linker=set(np.flatnonzero(np.abs(displacement[:,2])<.1).tolist())
    near=c-box/2;near-=np.round(near/box)*box
    compact_linker=set(np.argsort(np.linalg.norm(near,axis=1))[:216].tolist())
    slab=set(np.flatnonzero(z[:,0]<20.7004-.01).tolist())
    specifications=[('l',random_sites(648,216)),('c',ordered_cluster),('l',random_sites(648,1)),
                    ('c',random_sites(108,27)),('l',ordered_linker),('c',random_sites(108,1)),
                    ('l',compact_linker),('c',slab),('l',random_sites(648,65))]
    masks = json.loads(Path(__file__).with_name('competing_linker_masks.json').read_text(encoding='utf-8'))
    specifications.extend(('l', set(masks[key])) for key in ('blocked_face', 'bridged_face', 'bridged_decoy', 'oblique_face'))
    out=ROOT/'environment/data/structures';out.mkdir(parents=True,exist_ok=True)
    reference=read(source);reference.info={};write(ROOT/'environment/data/reference.cif',reference)
    refpath=ROOT/'environment/data/reference.cif';refpath.write_bytes(refpath.read_bytes().replace(b'\r\n',b'\n'))
    records={}
    public_ids = (1, 10, 3, 4, 5, 6, 13, 8, 9, 2, 7, 11, 12)
    for idx,(family,missing) in zip(public_ids, specifications):
        removed_clusters=missing if family=='c' else set()
        removed_linkers=missing if family=='l' else {i for i,(a,b) in enumerate(ends) if a in missing or b in missing}
        keep=[i for i,(kind,k) in enumerate(owner) if not (kind=='c' and k in removed_clusters or kind=='l' and k in removed_linkers)]
        specimen=atoms[keep];specimen=specimen[rng.permutation(len(specimen))];specimen.info={}
        name=f'sample_{idx:02d}';dest=out/(name+'.cif');write(dest,specimen);dest.write_bytes(dest.read_bytes().replace(b'\r\n',b'\n'))
        # Evidence records are never in the Agent image.
        alive_z=[i for i in range(len(z)) if i not in removed_clusters]
        degree=Counter()
        for i,(a,b) in enumerate(ends):
            if i not in removed_linkers: degree[int(a)]+=1;degree[int(b)]+=1
        records[name]={'family':family,'removed_cluster_ids':sorted(removed_clusters),
            'removed_linker_ids':sorted(removed_linkers),'missing_centers_A':(z if family=='c' else c)[sorted(missing)].tolist(),
            'ideal_centers_A':(z if family=='c' else c).tolist(),
            'alive_cluster_ids':alive_z,'edges':[[int(a),int(b),(-np.rint((z[b]-c[i])/box)+np.rint((z[a]-c[i])/box)).astype(int).tolist()] for i,(a,b) in enumerate(ends) if i not in removed_linkers],
            'cluster_count':len(alive_z),'intact_linker_count':648-len(removed_linkers),
            'degree_histogram':{str(k):v for k,v in sorted(Counter(degree[i] for i in alive_z).items())},
            'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()}
    (ROOT/'authoring/evidence/generation_record.json').write_text(json.dumps(records,indent=2)+'\n')
    print({k:(v['family'],len(v['missing_centers_A']),v['cluster_count'],v['intact_linker_count']) for k,v in records.items()})
if __name__=='__main__': main()
