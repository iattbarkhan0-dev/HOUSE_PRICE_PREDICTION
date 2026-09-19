import os
import random
import joblib
class ModelManager:
    def __init__(self):
        self.models = {}
        self.active_version = "v2"
        self.ab_testing = False
        self.ab_versions = ["v2","v3"]
        self.traffic = {"v2": 50,"v3": 50}
        self.load_models()
        self.validate_models()
    def load_models(self):
        base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),"models")
        for version in ["v1","v2","v3"]:
            model_path = os.path.join(base_path,f"model_{version}.pkl")
            if not os.path.exists(model_path):
                print(f"WARNING: {model_path} not found")
                continue
            try:
                self.models[version] = joblib.load(model_path)
            except Exception as e:
                raise RuntimeError(f"Could not load {version}: {e}")
    def validate_models(self):
        if not self.models:
            raise RuntimeError("No models were loaded.")
        if self.active_version not in self.models:
            raise RuntimeError(f"Active model {self.active_version} is not available.")
    def get_versions(self):
        return list(self.models.keys())
    def switch_model(self, version):
        if version not in self.models:
            raise ValueError(f"Model {version} does not exist")
        self.active_version = version
    def get_model(self):
        if self.ab_testing:
            versions = list(self.traffic.keys())
            weights = list(self.traffic.values())
            version = random.choices(versions,weights=weights,k=1)[0]
        else:
            version = self.active_version
        if version not in self.models:
            raise RuntimeError(f"Model {version} is not loaded")
        return (version,self.models[version])
    def enable_ab_testing(self,version1,version2,percentage1=50,percentage2=50):
        if version1 not in self.models:
            raise ValueError(f"{version1} does not exist")
        if version2 not in self.models:
            raise ValueError(f"{version2} does not exist")
        if version1 == version2:
            raise ValueError("A/B testing requires two different model versions")
        if percentage1 < 0 or percentage2 < 0:
            raise ValueError("Traffic percentages cannot be negative")
        if not abs((percentage1 + percentage2) - 100) < 1e-6:
            raise ValueError("Traffic percentages must equal 100")
        self.ab_versions = [version1,version2]
        self.traffic = {version1: percentage1,version2: percentage2}
        self.ab_testing = True
    def disable_ab_testing(self):
        self.ab_testing = False 


    
   
   
 
 
 
 
                
 
