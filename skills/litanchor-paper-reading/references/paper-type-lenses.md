# Paper-type analytical lenses

Apply one primary analytical lens from the paper's argument, not its discipline.
Apply at most one secondary lens only when a second contribution has substantial
independent evidence. These lenses refine extraction and recall review; they do
not replace the stable `paper_type` machine enum.

## Methods and systems

- Reconstruct input, output, modules, training or transformation, inference,
  external tools, feedback loops and cost.
- Separate the core insight from the implementation bundle.
- Map each ablation to one component and check baseline, data and budget parity.
- Treat an intended module role as an author claim until an isolation experiment
  supports it.

## Discovery and mechanism

- Separate association, temporal order, necessity, sufficiency and mechanism.
- Identify interventions, controls, replication and plausible alternatives.
- Check measurement validity, scale, model-system limits and generalization.
- Do not infer mechanism from correlation or a phenotype alone.

## Resource, dataset and benchmark

- Record construction, inclusion/exclusion, annotation, preprocessing, splits,
  access, licensing and intended use.
- Check representativeness, missingness, label quality, contamination, leakage
  and whether the metric measures the claimed capability.
- Separate evidence that a resource is large from evidence that it is useful,
  valid and generalizable.

## Clinical and population

- Record population, setting, enrollment, exposure or intervention, comparator,
  outcomes, follow-up, missing data and analysis set.
- Separate prespecified from exploratory outcomes, relative from absolute effects
  and statistical significance from practical benefit.
- Check confounding, multiplicity, calibration, external validation, attrition
  and studied-population boundaries.

## Materials and engineering

- Record composition, preparation or fabrication, processing conditions,
  characterization, operating environment and comparator.
- Reconstruct the structure -> property -> mechanism -> performance chain.
- Check uncertainty, batch variation, durability, scale-up, realistic conditions
  and metric normalization.
- Separate demonstrated mechanism from post-hoc interpretation.

## Review and evidence synthesis

- Record scope, search or selection method, inclusion/exclusion, taxonomy,
  synthesis method and intended contribution.
- For systematic reviews or meta-analyses, check protocol, heterogeneity, risk of
  bias, publication bias and sensitivity analysis.
- For narrative reviews or perspectives, separate evidence synthesis from author
  framing and advocacy.
- Replace ablation questions with coverage, counterexample and omitted-literature
  checks; citation volume is not evidence quality.

## Completion criterion

Before recall review, every primary-lens check that applies to the paper must be
represented by verified evidence, an explicit `原文未说明`, or an explicit
`不适用`. A secondary lens must add a distinct check rather than duplicate the
primary analysis.
