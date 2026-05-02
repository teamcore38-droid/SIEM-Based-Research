import pickle, os, warnings
warnings.filterwarnings('ignore')

MODELS_DIR = 'models'
files = ['ARS Action.pkl', 'ars_response_model.pkl', 'ars_phi_model.pkl', 
         'ars_decision_model_final.pkl', 'ARS PHI.pkl']

for mf in files:
    path = os.path.join(MODELS_DIR, mf)
    if not os.path.exists(path):
        print(f'{mf} -> NOT FOUND')
        continue
    with open(path, 'rb') as f:
        obj = pickle.load(f)
    tp = type(obj).__name__
    print(f'\n=== {mf} === (type: {tp})')
    if isinstance(obj, dict):
        for k in obj:
            v = obj[k]
            vt = type(v).__name__
            extras = []
            if hasattr(v, 'classes_'):
                extras.append(f'classes={list(v.classes_)}')
            if hasattr(v, 'n_features_in_'):
                extras.append(f'n_features={v.n_features_in_}')
            extra_str = ' | '.join(extras) if extras else ''
            print(f'  {k}: {vt} {extra_str}')
    elif hasattr(obj, 'classes_'):
        print(f'  classes: {list(obj.classes_)}')
        if hasattr(obj, 'n_features_in_'):
            print(f'  n_features: {obj.n_features_in_}')
        if hasattr(obj, 'feature_names_in_'):
            print(f'  features: {list(obj.feature_names_in_)[:10]}...')
    elif hasattr(obj, 'predict'):
        print(f'  Has predict: yes')
    else:
        print(f'  Preview: {str(obj)[:300]}')
