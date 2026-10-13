# Model Card: MC-S1-AWD-01 (Sentinel-1 SAR Water Status Detector)

## Model Overview
- **Model Name:** Sentinel-1 Synthetic Aperture Radar Alternate Wetting & Drying Water Status Classifier
- **Model Identifier:** `MC-S1-AWD-01`
- **Version:** 1.0 (Adaptive Backscatter Thresholding Baseline)
- **Primary Task:** Binary / Multi-class water regime classification of irrigated rice paddies into `FLOODED`, `DRAINED_AWD`, or `DRY_AERATED`.
- **Maintainer:** CarbonKheti ML & Geospatial Engineering Team

## Physical & Algorithmic Basis
1. **Radar Physics:** C-band Synthetic Aperture Radar (SAR, 5.405 GHz) backscatter coefficients ($\sigma^0$ or $\gamma^0$) in copolarized (VV) and cross-polarized (VH) channels respond to surface roughness and dielectric constant.
2. **Specular Reflection:** Standing open water acts as a specular reflector, resulting in very low return energy (VV $\le -15.5\text{ dB}$).
3. **Aeration Status:** Aerated/drained moist soil exhibits diffuse surface scattering with a $+3\text{ dB}$ to $+6\text{ dB}$ increase in backscatter.
4. **Adaptive Thresholding:** Backscatter thresholds are adjusted per orbital pass against baseline pre-season minimums and calibrated with field AWD water tube readings.

## Training & Validation Data
- **Current Status:** Calibrated on peer-reviewed IRRI/IWMI published SAR trial benchmarks across Indian and Southeast Asian rice ecologies.
- **Empirical Ground Truth Accumulation:** Regional training observations are currently accumulating from registered farmer AWD tube readings.
- **Honest Metrics Disclosure:** In accordance with CarbonKheti Rule 0, zero fabricated accuracy or precision/recall metrics are reported. Regional LightGBM model will be published after accumulating $N \ge 500$ verified field ground-truth tube checkpoints.

## Limitations & Edge Cases
- Severe rainstorms immediately preceding a satellite pass create temporary standing water, registering as flooded even if soil was aerated.
- Dense mature vegetative canopy (near heading/grain-filling) causes volume scattering, muting ground soil backscatter contrast.
- Optical Sentinel-2 NDVI time series harmonic fit is used in fusion to resolve canopy interference.
