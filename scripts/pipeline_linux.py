# =============================================================================
# PROYECTO BIG DATA — UPeU 2026-1  [VERSIÓN LINUX / Ubuntu 24.04]
# Pipeline: Ingesta → Transformación → JOIN Triple → Parquet → ML
# Host: bigdata-core | 7.8 GB RAM | 4 vCPUs
# =============================================================================

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.ml.feature import StringIndexer, VectorAssembler, StandardScaler
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml import Pipeline
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder
import pandas as pd
import os
import time

# =============================================================================
# 0. RUTAS (Linux — sin espacios)
# =============================================================================
HOME   = os.path.expanduser("~")
BASE   = os.path.join(HOME, "bigdata", "tablas")
OUTPUT = os.path.join(HOME, "bigdata", "output")

T1_PATH = os.path.join(BASE, "T1_global_threats.csv")
T2_PATH = os.path.join(BASE, "T2_ai_ml_events.csv")
T3_PATH = os.path.join(BASE, "T3_synthesized.csv")

VALID_ATTACK_TYPES = ["DDoS", "Malware", "Man-in-the-Middle",
                      "Phishing", "Ransomware", "SQL Injection"]

start_total = time.time()

# =============================================================================
# 1. INGESTA CON PANDAS
# =============================================================================
print("\n" + "="*60)
print("[FASE 1] INGESTA")
print("="*60)
t0 = time.time()

pd_t1 = pd.read_csv(T1_PATH)
pd_t2 = pd.read_csv(T2_PATH)
pd_t3_full = pd.read_csv(T3_PATH)

pd_t3 = (pd_t3_full[pd_t3_full["attack_type"].isin(VALID_ATTACK_TYPES)]
         .sample(n=6000, random_state=42)
         .reset_index(drop=True))

print(f"  T1: {len(pd_t1):>7,} filas x {len(pd_t1.columns)} cols")
print(f"  T2: {len(pd_t2):>7,} filas x {len(pd_t2.columns)} cols")
print(f"  T3: {len(pd_t3):>7,} filas x {len(pd_t3.columns)} cols (pre-filtrado de {len(pd_t3_full):,})")
print(f"  Tiempo ingesta: {time.time()-t0:.1f}s")

# =============================================================================
# 2. SPARK SESSION — config ajustada para 7.8 GB RAM / 4 vCPUs
# =============================================================================
print("\n[FASE 2] SPARK SESSION")

spark = (SparkSession.builder
         .appName("BigData_UPeU_Pipeline")
         .master("local[*]")
         .config("spark.driver.memory",          "5g")
         .config("spark.driver.maxResultSize",   "2g")
         .config("spark.sql.shuffle.partitions", "4")
         .config("spark.memory.fraction",        "0.8")
         .config("spark.memory.storageFraction", "0.3")
         .getOrCreate())

spark.sparkContext.setLogLevel("ERROR")
print(f"  Spark {spark.version} iniciado")
print(f"  Cores disponibles: {spark.sparkContext.defaultParallelism}")

t1_raw = spark.createDataFrame(pd_t1)
t2_raw = spark.createDataFrame(pd_t2)
t3_raw = spark.createDataFrame(pd_t3)

# =============================================================================
# 3. TRANSFORMACION T1
# =============================================================================
print("\n[FASE 3] TRANSFORMACION")

t1 = (t1_raw
      .withColumnRenamed("Attack Type",                        "Attack_Type")
      .withColumnRenamed("Target Industry",                    "Target_Industry")
      .withColumnRenamed("Financial Loss (in Million $)",      "Financial_Loss_M")
      .withColumnRenamed("Number of Affected Users",           "Affected_Users")
      .withColumnRenamed("Attack Source",                      "Attack_Source")
      .withColumnRenamed("Security Vulnerability Type",        "Vulnerability_Type")
      .withColumnRenamed("Defense Mechanism Used",             "Defense_Mechanism")
      .withColumnRenamed("Incident Resolution Time (in Hours)","Resolution_Hours"))

print(f"  T1: {t1.count()} filas")

# =============================================================================
# 4. TRANSFORMACION T2
# =============================================================================
t2_clean = (t2_raw
            .withColumn("Year", F.year(F.to_timestamp("Timestamp")))
            .withColumnRenamed("Attack Type",        "Attack_Type")
            .withColumnRenamed("Attack Severity",    "Attack_Severity")
            .withColumnRenamed("Event ID",           "Event_ID")
            .withColumnRenamed("Source IP",          "Source_IP")
            .withColumnRenamed("Destination IP",     "Destination_IP")
            .withColumnRenamed("User Agent",         "User_Agent")
            .withColumnRenamed("Data Exfiltrated",   "Data_Exfiltrated")
            .withColumnRenamed("Threat Intelligence","Threat_Intel")
            .withColumnRenamed("Response Action",    "Response_Action")
            .filter(F.col("Attack_Type").isin(VALID_ATTACK_TYPES))
            .filter(F.col("Year").isNotNull()))

t2_sampled = t2_clean.sample(fraction=0.25, seed=42)
print(f"  T2 sampled: {t2_sampled.count()} filas")

# =============================================================================
# 5. TRANSFORMACION T3
# =============================================================================
t3_clean = (t3_raw
            .withColumn("Year", F.year(F.to_timestamp("timestamp")))
            .filter(F.col("Year").isNotNull()))

t3_sampled = t3_clean
print(f"  T3: {t3_sampled.count()} filas (pre-filtrado en pandas)")

# =============================================================================
# 6. AGREGACION PRE-JOIN
# =============================================================================
print("\n[FASE 4] AGREGACION")

t2_agg = (t2_sampled
          .groupBy("Attack_Type", "Year")
          .agg(
              F.count("Event_ID")                           .alias("t2_total_eventos"),
              F.avg(F.when(F.col("Attack_Severity")=="Low",    1)
                     .when(F.col("Attack_Severity")=="Medium", 2)
                     .when(F.col("Attack_Severity")=="High",   3)
                     .when(F.col("Attack_Severity")=="Critical",4)
                     .cast("double"))                          .alias("t2_avg_severity"),
              F.sum(F.col("Data_Exfiltrated").cast("integer"))
                                                            .alias("t2_exfiltrations"),
              F.countDistinct("Source_IP")                  .alias("t2_unique_ips"),
          ))

t3_agg = (t3_sampled
          .groupBy("attack_type")
          .agg(
              F.count("attacker_ip")              .alias("t3_total_sesiones"),
              F.avg("data_compromised_GB")         .alias("t3_avg_data_GB"),
              F.avg("attack_duration_min")         .alias("t3_avg_duration_min"),
              F.avg("attack_severity")             .alias("t3_avg_severity"),
              F.avg("response_time_min")           .alias("t3_avg_response_min"),
              F.countDistinct("mitigation_method") .alias("t3_mitigations_count"),
          )
          .withColumnRenamed("attack_type", "Attack_Type"))

print(f"  T2_agg: {t2_agg.count()} combinaciones (Attack_Type x Year)")
print(f"  T3_agg: {t3_agg.count()} filas unicas por Attack_Type")

# =============================================================================
# 7. JOIN TRIPLE — T1 LEFT JOIN T2_agg LEFT JOIN T3_agg
# =============================================================================
print("\n[FASE 5] JOIN TRIPLE")
t0 = time.time()

join1     = t1.join(t2_agg, on=["Attack_Type", "Year"], how="left")
resultado = join1.join(t3_agg, on="Attack_Type",        how="left")

rc       = resultado.count()
match_t2 = resultado.filter(F.col("t2_total_eventos").isNotNull()).count()
match_t3 = resultado.filter(F.col("t3_total_sesiones").isNotNull()).count()

print(f"  Filas resultado: {rc:,}  (T1 original: {t1.count():,}) <- deben ser iguales")
print(f"  Cobertura T2:   {match_t2:,} filas ({match_t2/rc*100:.1f}%)")
print(f"  Cobertura T3:   {match_t3:,} filas ({match_t3/rc*100:.1f}%)")
print(f"  Tiempo JOIN: {time.time()-t0:.1f}s")

print("\n  [MUESTRA — 5 filas]")
resultado.select(
    "Country","Year","Attack_Type","Financial_Loss_M",
    "t2_total_eventos","t2_avg_severity","t3_avg_data_GB"
).show(5, truncate=False)

# =============================================================================
# 8. ESCRITURA PARQUET
# =============================================================================
print("\n[FASE 6] ESCRITURA PARQUET")
t0 = time.time()

parquet_path = os.path.join(OUTPUT, "cybersecurity_joined")
(resultado.write
          .mode("overwrite")
          .partitionBy("Attack_Type", "Year")
          .parquet(parquet_path))

df_check = spark.read.parquet(parquet_path)
print(f"  Parquet escrito: {df_check.count():,} filas OK")
print(f"  Ruta: {parquet_path}")
print(f"  Tiempo escritura: {time.time()-t0:.1f}s")

# =============================================================================
# 9. EDA POST-JOIN
# =============================================================================
print("\n[FASE 7] ANALISIS EXPLORATORIO")

print("\n  Top Attack Types por perdida financiera promedio (USD M):")
resultado.groupBy("Attack_Type") \
    .agg(F.avg("Financial_Loss_M").alias("avg_loss_M"),
         F.sum("Affected_Users").alias("total_afectados")) \
    .orderBy(F.desc("avg_loss_M")).show(6, truncate=False)

print("  Incidentes y perdidas por anio:")
resultado.groupBy("Year") \
    .agg(F.sum("Financial_Loss_M").alias("total_loss_M"),
         F.count("*").alias("incidentes")) \
    .orderBy("Year").show(10)

print("  Severidad (T2) vs datos comprometidos GB (T3) por Attack Type:")
resultado.groupBy("Attack_Type") \
    .agg(F.avg("t2_avg_severity").alias("severidad_eventos"),
         F.avg("t3_avg_data_GB").alias("datos_comprometidos_GB")) \
    .orderBy("Attack_Type").show(6, truncate=False)

# =============================================================================
# 10. ML PIPELINE — RANDOM FOREST CLASSIFIER
# =============================================================================
print("\n[FASE 8] ML PIPELINE — RandomForest Classifier")

feature_cols = ["data_compromised_GB", "attack_duration_min",
                "attack_severity", "response_time_min"]

ml_data  = t3_sampled.select(["attack_type"] + feature_cols).dropna()
train_df, test_df = ml_data.randomSplit([0.8, 0.2], seed=42)
print(f"  Train: {train_df.count():,} | Test: {test_df.count():,}")

indexer   = StringIndexer(inputCol="attack_type", outputCol="label", handleInvalid="skip")
assembler = VectorAssembler(inputCols=feature_cols, outputCol="features_raw")
scaler    = StandardScaler(inputCol="features_raw", outputCol="features",
                           withMean=True, withStd=True)
rf        = RandomForestClassifier(labelCol="label", featuresCol="features", seed=42)
pipeline  = Pipeline(stages=[indexer, assembler, scaler, rf])

param_grid = (ParamGridBuilder()
              .addGrid(rf.numTrees, [50, 100])
              .addGrid(rf.maxDepth, [5, 10])
              .build())

evaluator = MulticlassClassificationEvaluator(
    labelCol="label", predictionCol="prediction", metricName="f1")

cv = CrossValidator(estimator=pipeline, estimatorParamMaps=param_grid,
                    evaluator=evaluator, numFolds=3, seed=42)

print("  Entrenando CrossValidator (4 combinaciones x 3 folds = 12 runs)...")
t0 = time.time()
cv_model = cv.fit(train_df)
print(f"  Entrenamiento completado en {time.time()-t0:.1f}s")

predictions = cv_model.transform(test_df)
f1  = evaluator.evaluate(predictions)
acc = MulticlassClassificationEvaluator(
        labelCol="label", predictionCol="prediction",
        metricName="accuracy").evaluate(predictions)

best_rf = cv_model.bestModel.stages[-1]
print(f"\n  +---------------------------+")
print(f"  |  METRICAS FINALES         |")
print(f"  +---------------------------+")
print(f"  |  F1-Score (macro): {f1:.4f} |")
print(f"  |  Accuracy:         {acc:.4f} |")
print(f"  |  Mejor numTrees:   {best_rf.getNumTrees:<6} |")
print(f"  |  Mejor maxDepth:   {best_rf.getOrDefault('maxDepth'):<6} |")
print(f"  +---------------------------+")

print("\n  Distribucion de predicciones:")
predictions.groupBy("attack_type", "prediction").count() \
    .orderBy("attack_type").show(truncate=False)

# =============================================================================
# CIERRE
# =============================================================================
elapsed = time.time() - start_total
print(f"\n{'='*60}")
print(f"  PIPELINE COMPLETO — OK")
print(f"  Tiempo total: {elapsed/60:.1f} min ({elapsed:.0f}s)")
print(f"  Parquet: {parquet_path}")
print(f"{'='*60}\n")

spark.stop()
