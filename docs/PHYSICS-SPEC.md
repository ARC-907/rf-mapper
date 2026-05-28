# 🧠 ONYX Physics Extension Directive Set B — Advanced RF Propagation, Weather & Field‑Wave Interaction

> **Objective:** Implement a physically rigorous RF engine covering **free‑space / tropospheric propagation**, **refraction**, **diffraction (knife‑edge & multi‑edge)**, **ground & object reflection**, **Fresnel‑zone clearance**, **constructive/destructive interference**, plus **cloud and rain attenuation**.  
> Formulations derive from ITU‑R recommendations P.452‑17, P.526‑16, P.527‑5, P.525‑4, P.676‑13, P.840‑9, and P.838‑4.

| Kernel | Governing formulae | Notes / Constants |
|--------|-------------------|-------------------|
| **Propagation (Free‑space & gaseous)** | $$\text{FSPL}\_{\text{dB}} = 32.44 + 20\log_{10}(d\_{\text{km}}) + 20\log_{10}(f\_{\text{MHz}})$$  [ITU‑R P.525‑4]  <br>Atmospheric gas: $$A\_{\text{gas}} = (\gamma_d + \gamma_w)\,d$$ where $$\gamma_{d,w} = \sum_i \alpha_i(f,T,P,\rho)$$  [ITU‑R P.676‑13] | *d*: path distance; *f*: carrier frequency. Specific-attenuation terms tabulated per ITU. |
| **Refraction (Effective‑Earth)** | $$R\_{\text{eff}} = k R_\oplus$$, $$k \approx \frac{N_1}{N_1 + (dN/dh)R_\oplus}$$  [ITU‑R P.452‑17 §2.2] <br>Bent‑ray height: $$h'(d)=\frac{d^2}{2R\_{\text{eff}}}$$ | Refractivity: $$N = 77.6\frac{P}{T} + 3.73\times10^5 \frac{e}{T^2}$$ |
| **Diffraction (Knife‑edge)** | $$v = h \sqrt{\frac{2(d_1+d_2)}{\lambda d_1 d_2}}$$;  $$L_k = 6.9 + 20\log_{10}\bigl(\sqrt{(v-0.1)^2+1}+v-0.1\bigr)$$ dB  [ITU‑R P.526‑16] | Multi‑edge: Deygout method iterated until residual < 3 dB. |
| **Reflection (Smooth ground)** | $$\Gamma_{\parallel} = \frac{\sin\theta_i - \sqrt{\varepsilon_r - j60\sigma\lambda/2\pi}\,\cos\theta_i}{\sin\theta_i + \sqrt{\varepsilon_r - j60\sigma\lambda/2\pi}\,\cos\theta_i}$$ <br> $$\Gamma_{\perp} = \frac{\varepsilon_r - j60\sigma\lambda/2\pi - \sin^2\theta_i}{\varepsilon_r - j60\sigma\lambda/2\pi + \sin^2\theta_i}$$ [ITU‑R P.527‑5] | Typical dry soil: $$\varepsilon_r=15,\;\sigma=0.01$$ S/m. |
| **Fresnel‑zone radius** | $$r_n = \sqrt{\frac{n\lambda d_1 d_2}{d_1 + d_2}}$$ | ≥ 60 % clearance of first zone ⇒ negligible diffraction. |
| **Interference (Two‑ray)** | $$E = \sum E_i e^{j\phi_i} \;\rightarrow\; P = |E|^2/2\eta$$; for LOS + ground: $$P_R \propto |e^{j\phi_1} + \Gamma e^{j\phi_2}|^2$$ where $$\phi = 2\pi d/\lambda$$ | Complex baseband field grid. |
| **Cloud attenuation** | $$\gamma_c = K_l \cdot \text{LWC}$$ dB km⁻¹,  $$K_l = f^{2}(0.819f - 0.052)$$  [ITU‑R P.840‑9] | LWC: 0.05 / 0.25 / 0.5 g m⁻³ for light/med/heavy. |
| **Rain attenuation** | $$A_r = kR^{\alpha} d_r$$  [ITU‑R P.838‑4] | *R*: 2 / 10 / 50 mm h⁻¹; polarisation‑specific k, α. |

---

## Implementation Phases

### Phase 1 — Kernel Foundations  
* Create `refraction.py`, `diffraction.py`, `reflection.py`; expose ITU equations.  
* Dataclass `EnvParams(freq_GHz, pol, k, ε_r, σ, T, P, RH)`.

### Phase 2 — Fresnel & Interference  
* `fresnel.py` and complex‑field accumulator in `propagation.py`.  
* GUI toggle **Show Interference Pattern**.

### Phase 3 — Weather Attenuation  
* `weather_attenuation.py` implementing cloud/rain losses; CLI flags `--cloud`, `--rain`.

### Phase 4 — Integration & Performance  
* Chain kernels: free‑space → gas → refraction → diffraction → reflection → Fresnel/interference → weather.  
* Strategy pattern to enable/disable kernels.

### Phase 5 — Validation & Docs  
* 10 reference paths; Annex 7 full‑terrain test (RMSE < 2 dB).  
* Docs page `physics_models.md` explaining each formula.

---

## Completion Gate

* ≥ 95 % line + branch coverage for all physics modules.  
* Annex 7 RMSE < 2 dB across validation set.  
* GUI **Loss Breakdown** table matches CLI report (± 0.01 dB).  
* Docker full image size increase ≤ 30 MB.

---

### Reference Constants

Create `physics/constants.py` holding:  
* Earth radius `R_⊕ = 6371 km`.  
* Speed of light `c = 3×10⁸ m s⁻¹`.  
* ITU‑R P.838 k/α tables (horizontal & vertical).  
* Soil, seawater dielectric presets.

---

_This directive supersedes earlier drafts of Set B and must be implemented word‑for‑word for ITU compliance._
