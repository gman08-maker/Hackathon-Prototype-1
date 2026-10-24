"""Tab: where the data comes from and what it can't tell you."""

import streamlit as st

import config

ABOUT = f"""
### Data

- **Source:** U.S. Department of Education, College Scorecard, *Most Recent
  Institution-Level Data* (downloaded October 2026). Different measures come from
  different student cohorts; see the Scorecard documentation for exact years.
- **License:** Public domain (U.S. government work).
- **Which schools:** Open public and private nonprofit colleges that mainly award
  bachelor's degrees, with a reported graduation rate and 10-year earnings, and a
  graduation-rate cohort of at least {config.MIN_GRAD_COHORT} students.
- **No commercial rankings were scraped.** "Prestige" is our own stand-in built from
  admit rate, average SAT, faculty salary and instructional spending per student.

### Method

- **Score:** each measure becomes a percentile (0 = worst school, 100 = best). Your
  weights average those percentiles. A missing value counts as the 50th percentile.
- **Financial fit:** you can weigh published tuition and fees, average net price, and
  median debt separately, or apply optional maximum-price filters. These are
  institution-level figures, not a student's expected bill or financial-aid offer.
  Aid eligibility, grant amounts, housing, books, transportation and personal budget
  are not available in this dataset.
- **Overperformers:** a random forest predicts graduation rate and earnings from
  student and resource inputs. Every prediction comes from a model that did not see
  that school (5-fold cross-validation). Actual minus predicted = overperformance.
- **Fragility:** 500 runs, each weight nudged randomly by up to ±20% (adjustable).

### Limitations, please read

- **Earnings only cover students who got federal financial aid**, and only those
  working and not enrolled. Earnings also depend on majors (arts schools look worse)
  and on local job markets, not just the college.
- **Correlation, not causation.** "Beats the prediction" means beats *our* model,
  which sees only 7 inputs. Things we can't measure (motivation, family wealth beyond
  Pell, program mix) can make a school look better or worse.
- **Small schools are under-represented.** The government hides (suppresses) values
  for small groups to protect privacy, and we drop schools with tiny cohorts.
- **Graduation rates only count first-time, full-time students**, so schools with many
  transfer or part-time students are only partly described.
- **A single score hides trade-offs.** The weights are value judgments: change them
  and the "best" school changes. That is the point of the fragility tab.
- **Faculty salary in the source data is monthly**, and SAT is missing for many
  test-optional schools; the prestige score uses whatever parts a school reports.
"""


def render():
    st.subheader("About the data & limitations")
    st.markdown(ABOUT)
