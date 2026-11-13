import yaml
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier

def load_model_config(config_path="config/model.yaml"):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def build_model(model_name: str, config_path="config/model.yaml"):
    cfg = load_model_config(config_path)
    model_name = model_name.lower()
    
    if model_name in ["mlp", "neural_network"]:
        mlp_cfg = cfg["mlp"]
        return MLPClassifier(
            hidden_layer_sizes=tuple(mlp_cfg["hidden_layer_sizes"]),
            activation=mlp_cfg["activation"],
            solver=mlp_cfg["solver"],
            alpha=mlp_cfg["alpha"],
            batch_size=mlp_cfg["batch_size"],
            learning_rate=mlp_cfg["learning_rate"],
            learning_rate_init=mlp_cfg["learning_rate_init"],
            max_iter=mlp_cfg["max_iter"],
            early_stopping=mlp_cfg["early_stopping"],
            n_iter_no_change=mlp_cfg["n_iter_no_change"],
            random_state=mlp_cfg["random_state"]
        )
    elif model_name in ["random_forest", "rf"]:
        rf_cfg = cfg["random_forest"]
        return RandomForestClassifier(
            n_estimators=rf_cfg["n_estimators"],
            max_depth=rf_cfg["max_depth"],
            random_state=rf_cfg["random_state"],
            n_jobs=rf_cfg.get("n_jobs", -1)
        )
    elif model_name in ["logistic_regression", "lr"]:
        lr_cfg = cfg["logistic_regression"]
        return LogisticRegression(
            max_iter=lr_cfg["max_iter"],
            random_state=lr_cfg["random_state"]
        )
    else:
        raise ValueError(f"Unknown model architecture: {model_name}. Available: mlp, random_forest, logistic_regression")

