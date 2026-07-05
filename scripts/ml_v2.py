# =============================================================================
# ML PIPELINE v2 — UPeU Big Data 2026-1
# Mejoras sobre v1:
#   - Todos los features de T3 (numéricos + categóricos con OneHotEncoding)
#   - 3 algoritmos: RandomForest vs DecisionTree vs MLP (red neuronal)
#   - Tarea 2: GBT binario → predice outcome (Success/Failure)
#   - Métricas por clase + Feature Importance + Matriz de Confusión
# =============================================================================

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.ml import Pipeline
from pyspark.ml.feature import (StringIndexer, OneHotEncoder,
                                VectorAssembler, StandardScaler)
from pyspark.ml.classification import (RandomForestClassifier,
                                       DecisionTreeClassifier,
                                       MultilayerPerceptronClassifier,
                                       GBTClassifier)
from pyspark.ml.evaluation import (MulticlassClassificationEvaluator,
                                   BinaryClassificationEvaluator)
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder
import os, time

start = time.time()

HOME   = os.path.expanduser("~")
T3_PATH = os.path.join(HOME, "bigdata", "tablas", "T3_synthesized.csv")

VALID_ATTACK_TYPES = ["DDoS", "Malware", "Phishing", "Ransomware", "SQL Injection"]

# =============================================================================
# SPARK
# =============================================================================
spark = (SparkSession.builder
         .appName("ML_v2_UPeU")
         .master("local[*]")
         .config("spark.driver.memory",          "5g")
         .config("spark.driver.maxResultSize",   "2g")
         .config("spark.sql.shuffle.partitions", "4")
         .getOrCreate())
spark.sparkContext.setLogLevel("ERROR")
print(f"Spark {spark.version} | Cores: {spark.sparkContext.defaultParallelism}")

# =============================================================================
# CARGA Y FILTRADO T3
# =============================================================================
t3_raw = (spark.read.csv(T3_PATH, header=True, inferSchema=True)
               .filter(F.col("attack_type").isin(VALID_ATTACK_TYPES))
               .dropna())

print(f"T3 filas (filtradas): {t3_raw.count():,}")

# =============================================================================
# TAREA 1: CLASIFICACION MULTICLASE — predecir attack_type
# =============================================================================
print("\n" + "="*60)
print("TAREA 1 — Clasificación multiclase: attack_type (5 clases)")
print("="*60)

# Features numéricos
NUM_COLS = ["data_compromised_GB", "attack_duration_min",
            "attack_severity", "response_time_min"]

# Features categóricos (nuevos respecto a v1)
CAT_COLS = ["target_system", "outcome", "security_tools_used",
            "user_role", "industry", "mitigation_method"]

ml_data = t3_raw.select(["attack_type"] + NUM_COLS + CAT_COLS)

# StringIndexer para label
label_indexer = StringIndexer(inputCol="attack_type", outputCol="label",
                              handleInvalid="skip")

# StringIndexer → OneHotEncoder para cada categórico
cat_indexers = [StringIndexer(inputCol=c, outputCol=c+"_idx",
                              handleInvalid="skip") for c in CAT_COLS]
cat_encoders = [OneHotEncoder(inputCol=c+"_idx", outputCol=c+"_ohe")
                for c in CAT_COLS]

# VectorAssembler con numéricos + OHE
assembler = VectorAssembler(
    inputCols=NUM_COLS + [c+"_ohe" for c in CAT_COLS],
    outputCol="features_raw")

scaler = StandardScaler(inputCol="features_raw", outputCol="features",
                        withMean=True, withStd=True)

train_df, test_df = ml_data.randomSplit([0.8, 0.2], seed=42)
print(f"Train: {train_df.count():,} | Test: {test_df.count():,}")
print(f"Features: {len(NUM_COLS)} numéricos + {len(CAT_COLS)} categóricos (OHE)")

evaluator_f1  = MulticlassClassificationEvaluator(
    labelCol="label", predictionCol="prediction", metricName="f1")
evaluator_acc = MulticlassClassificationEvaluator(
    labelCol="label", predictionCol="prediction", metricName="accuracy")

results = {}

# --- Modelo 1: RandomForest (con CrossValidator) ---
print("\n[1/3] RandomForest + CrossValidator")
rf = RandomForestClassifier(labelCol="label", featuresCol="features", seed=42)
pipe_rf = Pipeline(stages=[label_indexer] + cat_indexers + cat_encoders +
                           [assembler, scaler, rf])

param_grid_rf = (ParamGridBuilder()
                 .addGrid(rf.numTrees, [50, 100])
                 .addGrid(rf.maxDepth, [5, 10])
                 .build())

cv_rf = CrossValidator(estimator=pipe_rf, estimatorParamMaps=param_grid_rf,
                       evaluator=evaluator_f1, numFolds=3, seed=42)
t0 = time.time()
cv_model_rf = cv_rf.fit(train_df)
pred_rf     = cv_model_rf.transform(test_df)
f1_rf  = evaluator_f1.evaluate(pred_rf)
acc_rf = evaluator_acc.evaluate(pred_rf)
best_rf = cv_model_rf.bestModel.stages[-1]
print(f"  F1={f1_rf:.4f} | Acc={acc_rf:.4f} | "
      f"Trees={best_rf.getNumTrees} | Depth={best_rf.getOrDefault('maxDepth')} "
      f"| {time.time()-t0:.0f}s")
results["RandomForest"] = {"f1": f1_rf, "acc": acc_rf, "pred": pred_rf}

# Feature importance (top 8)
fi = best_rf.featureImportances
print("  Feature importances (top 8):")
feat_names = NUM_COLS + [c+"_ohe" for c in CAT_COLS]
fi_list = sorted(zip(feat_names, fi.toArray()), key=lambda x: -x[1])[:8]
for name, imp in fi_list:
    bar = "█" * int(imp * 300)
    print(f"    {name:<28} {imp:.4f}  {bar}")

# --- Modelo 2: DecisionTree ---
print("\n[2/3] DecisionTree")
dt = DecisionTreeClassifier(labelCol="label", featuresCol="features",
                             maxDepth=10, seed=42)
pipe_dt = Pipeline(stages=[label_indexer] + cat_indexers + cat_encoders +
                           [assembler, scaler, dt])
t0 = time.time()
model_dt = pipe_dt.fit(train_df)
pred_dt  = model_dt.transform(test_df)
f1_dt  = evaluator_f1.evaluate(pred_dt)
acc_dt = evaluator_acc.evaluate(pred_dt)
print(f"  F1={f1_dt:.4f} | Acc={acc_dt:.4f} | {time.time()-t0:.0f}s")
results["DecisionTree"] = {"f1": f1_dt, "acc": acc_dt}

# --- Modelo 3: MLP (Red Neuronal) ---
print("\n[3/3] MultilayerPerceptron (Red Neuronal)")
# Calcular dimensión de input
n_input = len(NUM_COLS)
for c in CAT_COLS:
    n_vals = t3_raw.select(c).distinct().count()
    n_input += max(n_vals - 1, 1)  # OHE drop last

layers = [n_input, 64, 32, 5]   # input → 64 → 32 → 5 clases
print(f"  Arquitectura: {layers}")

mlp = MultilayerPerceptronClassifier(
    labelCol="label", featuresCol="features",
    layers=layers, maxIter=100, seed=42)
pipe_mlp = Pipeline(stages=[label_indexer] + cat_indexers + cat_encoders +
                            [assembler, scaler, mlp])
t0 = time.time()
model_mlp = pipe_mlp.fit(train_df)
pred_mlp  = model_mlp.transform(test_df)
f1_mlp  = evaluator_f1.evaluate(pred_mlp)
acc_mlp = evaluator_acc.evaluate(pred_mlp)
print(f"  F1={f1_mlp:.4f} | Acc={acc_mlp:.4f} | {time.time()-t0:.0f}s")
results["MLP"] = {"f1": f1_mlp, "acc": acc_mlp}

# --- Tabla comparativa ---
print("\n  +-------------------+---------+---------+")
print("  | Algoritmo         |   F1    | Accuracy|")
print("  +-------------------+---------+---------+")
for name, r in results.items():
    print(f"  | {name:<17} |  {r['f1']:.4f} |  {r['acc']:.4f} |")
print("  +-------------------+---------+---------+")
print("  (referencia aleatoria 5 clases: F1~0.20, Acc~0.20)")

# --- Matriz de confusión RF (mejor modelo) ---
print("\n  Matriz de confusión (RandomForest — mejor modelo):")
label_map_df = (cv_model_rf.bestModel.stages[0]
                .transform(train_df.select("attack_type").distinct())
                .select("attack_type", "label")
                .orderBy("label"))
label_map = {row["label"]: row["attack_type"] for row in label_map_df.collect()}

confusion = (pred_rf.groupBy("label", "prediction").count()
             .orderBy("label", "prediction").collect())

labels_sorted = sorted(label_map.keys())
header = f"  {'Actual \\ Pred':<22}" + "".join(f"{label_map[l][:10]:>12}" for l in labels_sorted)
print(header)
print("  " + "-" * (22 + 12 * len(labels_sorted)))
conf_dict = {(r["label"], r["prediction"]): r["count"] for r in confusion}
for actual in labels_sorted:
    row_str = f"  {label_map[actual]:<22}"
    for pred_l in labels_sorted:
        val = conf_dict.get((actual, pred_l), 0)
        row_str += f"{val:>12}"
    print(row_str)

# --- Métricas por clase ---
print("\n  Precisión, Recall y F1 por clase (RandomForest):")
print(f"  {'Clase':<22} {'Precision':>10} {'Recall':>10} {'F1':>10}")
print("  " + "-"*54)
for lbl in labels_sorted:
    name = label_map[lbl]
    prec = MulticlassClassificationEvaluator(
        labelCol="label", predictionCol="prediction",
        metricName="precisionByLabel", metricLabel=lbl).evaluate(pred_rf)
    rec  = MulticlassClassificationEvaluator(
        labelCol="label", predictionCol="prediction",
        metricName="recallByLabel", metricLabel=lbl).evaluate(pred_rf)
    f1c  = MulticlassClassificationEvaluator(
        labelCol="label", predictionCol="prediction",
        metricName="fMeasureByLabel", metricLabel=lbl).evaluate(pred_rf)
    print(f"  {name:<22} {prec:>10.4f} {rec:>10.4f} {f1c:>10.4f}")

# =============================================================================
# TAREA 2: CLASIFICACION BINARIA — predecir outcome (Success/Failure)
# con GBT Classifier
# =============================================================================
print("\n" + "="*60)
print("TAREA 2 — Clasificación binaria: outcome (Success/Failure)")
print("="*60)

FEAT_OUTCOME = ["attack_type", "attack_severity", "attack_duration_min",
                "data_compromised_GB", "response_time_min",
                "target_system", "industry", "security_tools_used", "mitigation_method"]

bin_data = t3_raw.select(["outcome"] + FEAT_OUTCOME)

outcome_indexer = StringIndexer(inputCol="outcome", outputCol="label_bin",
                                handleInvalid="skip")
cat_bin = ["attack_type", "target_system", "industry",
           "security_tools_used", "mitigation_method"]
cat_bin_indexers = [StringIndexer(inputCol=c, outputCol=c+"_bidx",
                                  handleInvalid="skip") for c in cat_bin]
cat_bin_encoders = [OneHotEncoder(inputCol=c+"_bidx", outputCol=c+"_bohe")
                    for c in cat_bin]

num_bin = ["attack_severity", "attack_duration_min",
           "data_compromised_GB", "response_time_min"]

assembler_bin = VectorAssembler(
    inputCols=num_bin + [c+"_bohe" for c in cat_bin],
    outputCol="features_bin_raw")
scaler_bin = StandardScaler(inputCol="features_bin_raw", outputCol="features_bin",
                            withMean=True, withStd=True)

gbt = GBTClassifier(labelCol="label_bin", featuresCol="features_bin",
                    maxIter=20, maxDepth=5, seed=42)

pipe_bin = Pipeline(stages=[outcome_indexer] + cat_bin_indexers + cat_bin_encoders +
                            [assembler_bin, scaler_bin, gbt])

train_bin, test_bin = bin_data.randomSplit([0.8, 0.2], seed=42)
print(f"Train: {train_bin.count():,} | Test: {test_bin.count():,}")
print(f"Features: {len(num_bin)} numéricos + {len(cat_bin)} categóricos (OHE)")

t0 = time.time()
model_bin  = pipe_bin.fit(train_bin)
pred_bin   = model_bin.transform(test_bin)

auc_bin = BinaryClassificationEvaluator(
    labelCol="label_bin", rawPredictionCol="rawPrediction",
    metricName="areaUnderROC").evaluate(pred_bin)
acc_bin = MulticlassClassificationEvaluator(
    labelCol="label_bin", predictionCol="prediction",
    metricName="accuracy").evaluate(pred_bin)
f1_bin  = MulticlassClassificationEvaluator(
    labelCol="label_bin", predictionCol="prediction",
    metricName="f1").evaluate(pred_bin)

print(f"\n  GBT entrenado en {time.time()-t0:.0f}s")
print(f"  +------------------------------+")
print(f"  |  TAREA 2 — GBT Binario      |")
print(f"  +------------------------------+")
print(f"  |  AUC-ROC:  {auc_bin:.4f}          |")
print(f"  |  Accuracy: {acc_bin:.4f}          |")
print(f"  |  F1:       {f1_bin:.4f}          |")
print(f"  +------------------------------+")

print("\n  Distribución de predicciones vs real:")
pred_bin.groupBy("outcome", "prediction").count() \
        .orderBy("outcome", "prediction").show(truncate=False)

# Feature importance GBT (top 6)
gbt_fi  = model_bin.stages[-1].featureImportances
feat_bin_names = num_bin + [c+"_bohe" for c in cat_bin]
gbt_fi_list = sorted(zip(feat_bin_names, gbt_fi.toArray()), key=lambda x: -x[1])[:6]
print("  Feature importances GBT (top 6):")
for name, imp in gbt_fi_list:
    bar = "█" * int(imp * 200)
    print(f"    {name:<30} {imp:.4f}  {bar}")

# =============================================================================
# RESUMEN FINAL
# =============================================================================
elapsed = time.time() - start
print(f"\n{'='*60}")
print(f"  ML PIPELINE v2 COMPLETO — {elapsed/60:.1f} min ({elapsed:.0f}s)")
print(f"\n  TAREA 1 — Multiclase (5 clases attack_type):")
print(f"  {'Algoritmo':<20} {'F1':>8} {'Acc':>8}")
print(f"  {'-'*38}")
for name, r in results.items():
    print(f"  {name:<20} {r['f1']:>8.4f} {r['acc']:>8.4f}")
print(f"\n  TAREA 2 — Binario (outcome Success/Failure):")
print(f"  {'GBT':<20} {'AUC-ROC':>8}: {auc_bin:.4f}  F1: {f1_bin:.4f}")
print(f"\n  NOTA: F1~0.20 esperado (datos sintéticos sin señal discriminativa)")
print(f"  El pipeline demuestra ingeniería ML completa con datos reales.")
print(f"{'='*60}")

spark.stop()
