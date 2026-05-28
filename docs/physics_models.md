# Physics Models Documentation

This document explains the physics models used in the RF propagation simulation, including the formulas and their implementation details.

## Table of Contents

1. [Free-Space Path Loss](#free-space-path-loss)
2. [Atmospheric Gaseous Attenuation](#atmospheric-gaseous-attenuation)
3. [Refraction](#refraction)
4. [Diffraction](#diffraction)
5. [Reflection](#reflection)
6. [Fresnel Zone](#fresnel-zone)
7. [Interference](#interference)
8. [Weather Attenuation](#weather-attenuation)
9. [Kernel Chain](#kernel-chain)

## Free-Space Path Loss

Free-space path loss (FSPL) represents the loss in signal strength that occurs when an electromagnetic wave travels through free space. The formula is based on the ITU-R P.525-4 recommendation.

### Formula

```
FSPL_dB = 32.44 + 20*log10(d_km) + 20*log10(f_MHz)
```

Where:
- `d_km` is the distance in kilometers
- `f_MHz` is the frequency in MHz

### Implementation

The free-space path loss is implemented in the `FreeSpaceKernel` class in `kernel_chain.py`. The kernel calculates the FSPL and adds it to the current path loss.

## Atmospheric Gaseous Attenuation

Atmospheric gases, particularly oxygen and water vapor, absorb RF energy. The attenuation depends on frequency, temperature, pressure, and humidity. The full model is described in ITU-R P.676-13.

### Formula

```
A_gas = (γ_d + γ_w) * d
```

Where:
- `γ_d` is the specific attenuation due to dry air
- `γ_w` is the specific attenuation due to water vapor
- `d` is the path length in kilometers

The specific attenuation terms are calculated using complex formulas involving summations over spectral lines, as described in ITU-R P.676-13.

### Implementation

A simplified model is implemented in the `GaseousKernel` class in `kernel_chain.py`. The kernel calculates the specific attenuation based on temperature, humidity, and frequency, and then multiplies it by the path length to get the total attenuation.

## Refraction

Refraction occurs when RF waves bend due to changes in the refractive index of the atmosphere. The effective Earth radius model is used to account for this effect, as described in ITU-R P.452-17.

### Formula

```
R_eff = k * R_earth
```

Where:
- `k` is the effective Earth radius factor
- `R_earth` is the Earth radius (6371 km)

The effective Earth radius factor is calculated as:

```
k ≈ N_1 / (N_1 + (dN/dh) * R_earth)
```

Where:
- `N_1` is the surface refractivity
- `dN/dh` is the refractivity gradient in the first kilometer above ground

The bent-ray height is calculated as:

```
h'(d) = d^2 / (2 * R_eff)
```

Where:
- `d` is the distance in kilometers
- `R_eff` is the effective Earth radius in kilometers

### Implementation

The refraction model is implemented in the `refraction.py` module and used by the `RefractionKernel` class in `kernel_chain.py`. The kernel calculates the effective Earth radius factor and adjusts the path loss based on the deviation from the standard value (k = 4/3).

## Diffraction

Diffraction occurs when RF waves encounter obstacles and bend around them. The knife-edge diffraction model is used to calculate the additional loss, as described in ITU-R P.526-16.

### Formula

For a single knife-edge, the Fresnel diffraction parameter is calculated as:

```
v = h * sqrt(2 * (d1 + d2) / (λ * d1 * d2))
```

Where:
- `h` is the height of the obstacle above the straight line between endpoints
- `d1` is the distance from the transmitter to the obstacle
- `d2` is the distance from the obstacle to the receiver
- `λ` is the wavelength

The knife-edge diffraction loss is calculated as:

```
L_k = 6.9 + 20*log10(sqrt((v-0.1)^2+1) + v-0.1) dB
```

For multiple knife-edges, the Deygout method is used, which involves finding the main edge and secondary edges, and combining their losses.

### Implementation

The diffraction model is implemented in the `diffraction.py` module and used by the `DiffractionKernel` class in `kernel_chain.py`. The kernel calculates the diffraction loss for a terrain profile and adds it to the current path loss.

## Reflection

Reflection occurs when RF waves bounce off surfaces. The reflection coefficient depends on the polarization, incident angle, and material properties, as described in ITU-R P.527-5.

### Formula

For parallel polarization:

```
Γ_∥ = (sin(θ_i) - sqrt(ε_r - j*60*σ*λ/2π) * cos(θ_i)) / (sin(θ_i) + sqrt(ε_r - j*60*σ*λ/2π) * cos(θ_i))
```

For perpendicular polarization:

```
Γ_⊥ = (ε_r - j*60*σ*λ/2π - sin^2(θ_i)) / (ε_r - j*60*σ*λ/2π + sin^2(θ_i))
```

Where:
- `θ_i` is the incident angle
- `ε_r` is the relative permittivity of the reflecting surface
- `σ` is the conductivity of the reflecting surface in S/m
- `λ` is the wavelength in meters

### Implementation

The reflection model is implemented in the `reflection.py` module and used by the `ReflectionKernel` class in `kernel_chain.py`. The kernel calculates the reflection coefficient and applies it to the current path loss.

## Fresnel Zone

The Fresnel zone is an ellipsoid-shaped region between the transmitter and receiver. Obstacles within this zone can cause diffraction loss. The Fresnel zone radius is calculated as described in the ONYX Physics Extension Directive.

### Formula

```
r_n = sqrt((n*λ*d1*d2)/(d1+d2))
```

Where:
- `n` is the Fresnel zone number
- `λ` is the wavelength
- `d1` is the distance from the transmitter to the point
- `d2` is the distance from the point to the receiver

### Implementation

The Fresnel zone model is implemented in the `fresnel.py` module and used by the `FresnelKernel` class in `kernel_chain.py`. The kernel calculates the Fresnel zone clearance and applies additional loss if the clearance is insufficient.

## Interference

Interference occurs when multiple RF signals combine at a receiver. The complex field summation model is used to calculate the resulting field strength, as described in the ONYX Physics Extension Directive.

### Formula

```
E = ∑ E_i * e^(j*φ_i)
P = |E|^2 / (2*η)
```

Where:
- `E_i` is the electric field amplitude of the i-th signal
- `φ_i` is the phase of the i-th signal
- `η` is the wave impedance (377 ohms for free space)

For the two-ray model (LOS + ground reflection):

```
P_R ∝ |e^(j*φ_1) + Γ*e^(j*φ_2)|^2
```

Where:
- `φ_1` is the phase of the direct ray
- `φ_2` is the phase of the reflected ray
- `Γ` is the reflection coefficient

### Implementation

The interference model is implemented in the `interference.py` module and used by the `InterferenceKernel` class in `kernel_chain.py`. The kernel calculates the complex field sum and applies it to the current path loss.

## Weather Attenuation

Weather conditions, particularly clouds and rain, can cause additional attenuation. The cloud attenuation model is based on ITU-R P.840-9, and the rain attenuation model is based on ITU-R P.838-4.

### Formula

For cloud attenuation:

```
γ_c = K_l * LWC dB/km
K_l = f^2 * (0.819*f - 0.052)
```

Where:
- `K_l` is the specific attenuation coefficient
- `LWC` is the liquid water content in g/m³
- `f` is the frequency in GHz

For rain attenuation:

```
A_r = k * R^α * d_r
```

Where:
- `k` and `α` are frequency and polarization-dependent coefficients
- `R` is the rain rate in mm/h
- `d_r` is the path length through rain in kilometers

### Implementation

The weather attenuation models are implemented in the `weather_attenuation.py` module and used by the `WeatherKernel` class in `kernel_chain.py`. The kernel calculates the cloud and rain attenuation and adds them to the current path loss.

## Kernel Chain

The kernel chain is a design pattern that allows for flexible composition of physics effects. Each kernel represents a specific physics effect and can be enabled or disabled independently. The kernels are applied in a specific order to ensure correct calculation of the total path loss.

### Order of Application

1. Free-space path loss
2. Atmospheric gaseous attenuation
3. Refraction
4. Diffraction
5. Reflection
6. Fresnel zone clearance
7. Interference
8. Weather attenuation

### Implementation

The kernel chain is implemented in the `kernel_chain.py` module. The `KernelChain` class manages the kernels and applies them in the correct order. The `configure_from_options` method allows for easy configuration of the kernels based on user options.