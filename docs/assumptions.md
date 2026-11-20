# Data Assumptions and Model Card

This project uses Chicago Food Inspections records to reproduce a data-quality audit and test whether information available before a routine inspection can help rank inspections by their likelihood of failure.

## Part A Data Scope and Cleaning

The original City of Chicago CSV contained **318,627 records and 17 columns**. The study window contains **37,489 records** with inspection dates from January 2023 through December 2024. Each row represents one inspection record. A facility can appear more than once. The date filter defines the study scope, and cleaning retained all 37,489 rows in that window.

| Field or check | Decision and reason |
| --- | --- |
| Inspection ID | Require an ID on every row and check for repeated IDs. The study window had zero missing IDs, zero repeated IDs, and zero exact duplicate rows. Repeated visits to the same facility are expected. |
| Inspection Date | Parse the original CSV dates with `%m/%d/%Y` before filtering. Reject missing or invalid dates so they cannot silently disappear from the study window. |
| Category labels | Trim surrounding spaces in `Facility Type`, `Risk`, `Inspection Type`, and `Results`. This changed neither the missing counts nor the number of distinct labels. Keep the 17 `Risk = All` records as a source category because its meaning is unconfirmed. Keep the 7 missing risk values separate. |
| Facility Type | Keep the 166 missing values in the cleaned data. Exclude them from the SQLite ranking of named facility types. Preserve the source categories unless there is evidence that two labels mean the same thing. |
| Violations | Preserve the 11,717 blanks as missing. The field was blank in 96.1% of `No Entry` records and in 172 `Fail` records. A blank does not establish whether violations occurred. |
| ZIP and licence number | Read as text to preserve their original formatting. Keep the 4 missing ZIP values and the 1 missing licence number. All populated values passed the format checks used in the project. Format checks do not establish that an identifier is correct. |
| Coordinates | Preserve 126 rows with both coordinates missing. No populated coordinate pairs were incomplete or outside the valid degree ranges. Those range checks do not establish that the coordinates identify the correct address. |

The SQLite ranking uses completed routine inspections with known facility types. The failure rate is the number of `Fail` outcomes divided by the number of completed routine inspections in the group. The minimum of 50 inspections per facility type reduces the influence of very small groups. Long Term Care had the highest observed rate among eligible groups (71 of 227, or 31.3%). Restaurants had the largest number of failures (2,808 of 11,039). These are descriptive comparisons. Differences in facility mix, inspection conditions, or reporting could affect them.

## Part B Model Card

### Intended Use and Scope

This is a coursework model for comparing tabular classifiers and demonstrating repeatable inference. It applies to Chicago routine inspections labelled `Canvass` that have a final result. Its performance does not support using it to schedule, skip, or enforce inspections.

The positive class is `Fail`. The negative class combines `Pass` and `Pass w/ Conditions` because the task is to predict outright failure. The modelling cohort contains **15,872 inspections**, including **4,009 failures**. It excludes 2,804 routine records with outcomes such as `No Entry` or `Out of Business`. The model therefore does not estimate whether an attempted inspection will proceed.

### Inputs and Preprocessing

The model uses facility type, risk category, ZIP, inspection month, and inspection weekday. Calendar features assume the planned inspection date is known at scoring time. The historical file gives the recorded date and does not establish when that date was available. `Results` defines the target, and `Violations` is recorded during the inspection. Both stay out of the feature set. Inspection IDs, licence numbers, and business names are not used as predictors.

The pipeline fills missing categorical values with an explicit `Missing` label, one-hot encodes categories, and ignores unseen labels at prediction time. It median-imputes and scales the numeric calendar features. Each model and each cross-validation fold fits its own preprocessing using only its training rows.

### Evaluation and Threshold

| Split | Period | Completed routine inspections | Failures |
| --- | --- | ---: | ---: |
| Training | January–December 2023 | 7,280 | 2,013 |
| Validation | January–June 2024 | 4,169 | 1,054 |
| Final test | July–December 2024 | 4,423 | 942 |

Chronological splitting tests whether models trained on earlier records can score later inspections. Forward-chaining cross-validation within 2023 compared a dummy baseline, logistic regression, and random forest. Logistic regression had the highest mean cross-validation average precision (0.439) and the highest validation average precision (0.299). Random forest was close on both measures (0.433 and 0.298). Average precision was the primary metric because it measures how well the model ranks outright failures across decision thresholds.

The threshold was chosen to flag about 20% of validation inspections as an illustrative review budget. The saved threshold is approximately 0.357. Inference uses the stored unrounded value. The final evaluation used the pipeline fitted on 2023 and the fixed threshold selected on validation.

| Final test measure | Result |
| --- | ---: |
| Average precision | 0.228 |
| Dummy average precision | 0.213 |
| ROC-AUC | 0.509 |
| Inspections flagged | 749 of 4,423 (16.9%) |
| Precision | 25.6% |
| Recall | 20.4% |
| F1 | 0.227 |
| True positives / false positives | 192 / 557 |
| False negatives / true negatives | 750 / 2,924 |

### Limitations and Risks

- The model showed little separation on the final test and missed 750 of 942 failures. Using its flags to prioritize inspection work could overlook many actual failures and send reviewers to many inspections that do not fail.
- Failure prevalence fell from 27.7% in training to 21.3% in the final test. This observed change, along with lower scores in later periods, makes extrapolation uncertain. The analysis does not identify the cause of the change.
- A facility can appear in multiple periods. The time split evaluates later records and does not measure performance specifically on establishments never seen during training.
- In validation, the model missed 761 of 1,011 failures in the high-risk group. The medium- and low-risk groups had only 33 and 10 failures, so their miss rates are unstable. This analysis does not establish comparable performance across risk groups or neighbourhoods.
- Inspection outcomes reflect what was recorded at a particular visit. A score is a model estimate for the defined outcome, and these results do not establish that the scores are calibrated probabilities.

### Saved Pipeline and Reproduction

The saved artifact is `models/chicago_inspection_failure.joblib`. It contains the fitted preprocessing and classifier, feature column names, and the decision threshold. It scored two fictional records in a fresh session, including one with a missing ZIP code. The examples verify that the artifact loads and produces predictions. The final test above measures predictive performance.

Keep the original CSV unchanged. See `docs/schema.md` for field details and `outputs/reports/` for the data-quality, model comparison, and final test files. Record the actual download date and applicable City of Chicago data-use terms in the README. The course submission should disclose the AI assistance used.

[City of Chicago Data Portal source dataset](https://data.cityofchicago.org/Health-Human-Services/Food-Inspections/4ijn-s7e5)
