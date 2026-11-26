"""Monte Carlo transport foton sederhana pada satu lapisan kulit.

Model ini memakai paket foton dengan berat yang sama. Pada setiap tumbukan,
paket foton diserap atau dihamburkan. Batas permukaan dianggap tidak memiliki
pantulan Fresnel; R hanya menghitung foton yang kembali keluar setelah hamburan.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class Result:
    """Ringkasan hasil simulasi Monte Carlo."""

    absorbed: float
    reflected: float
    transmitted: float
    unfinished: float
    depth_edges_mm: np.ndarray
    absorbed_by_depth: np.ndarray
    transmission_standard_error: float
    steps_used: int


def _sample_henyey_greenstein(
    rng: np.random.Generator, g: float, count: int
) -> tuple[np.ndarray, np.ndarray]:
    """Ambil cos(theta) dan azimut untuk hamburan Henyey-Greenstein."""
    u = rng.random(count)

    if abs(g) < 1e-10:
        cos_theta = 2.0 * u - 1.0
    else:
        ratio = (1.0 - g * g) / (1.0 - g + 2.0 * g * u)
        cos_theta = (1.0 + g * g - ratio * ratio) / (2.0 * g)

    cos_theta = np.clip(cos_theta, -1.0, 1.0)
    phi = 2.0 * np.pi * rng.random(count)
    return cos_theta, phi


def simulate_transport(
    num_photons: int,
    mu_a_per_mm: float,
    mu_s_reduced_per_mm: float,
    g: float,
    thickness_mm: float,
    seed: int = 42,
    depth_bins: int = 40,
    max_steps: int = 8000,
) -> Result:
    """Simulasikan foton pada slab homogen dengan berkas datang tegak lurus.

    Parameter optik yang diminta adalah mu_a, mu_s' dan g. Koefisien hamburan
    biasa yang dipakai dalam panjang lintasan dihitung dari
    mu_s' = mu_s * (1 - g).
    """
    if num_photons < 1:
        raise ValueError("Jumlah foton harus lebih besar dari nol.")
    if mu_a_per_mm < 0 or mu_s_reduced_per_mm < 0:
        raise ValueError("Koefisien optik tidak boleh negatif.")
    if not 0.0 <= g < 1.0:
        raise ValueError("g harus berada pada rentang 0 sampai kurang dari 1.")
    if thickness_mm <= 0:
        raise ValueError("Ketebalan harus lebih besar dari nol.")
    if depth_bins < 1 or max_steps < 1:
        raise ValueError("Jumlah bin dan langkah harus lebih besar dari nol.")

    rng = np.random.default_rng(seed)
    edges = np.linspace(0.0, thickness_mm, depth_bins + 1)
    absorbed_by_depth = np.zeros(depth_bins, dtype=np.int64)

    # Relasi antara reduced scattering dan scattering biasa.
    mu_s_per_mm = mu_s_reduced_per_mm / (1.0 - g)
    mu_t_per_mm = mu_a_per_mm + mu_s_per_mm

    if mu_t_per_mm == 0.0:
        return Result(
            absorbed=0.0,
            reflected=0.0,
            transmitted=1.0,
            unfinished=0.0,
            depth_edges_mm=edges,
            absorbed_by_depth=absorbed_by_depth,
            transmission_standard_error=0.0,
            steps_used=0,
        )

    z = np.zeros(num_photons, dtype=np.float64)
    uz = np.ones(num_photons, dtype=np.float64)  # sumber kolimasi ke arah +z
    alive = np.ones(num_photons, dtype=bool)
    n_absorbed = 0
    n_reflected = 0
    n_transmitted = 0
    steps_used = 0

    for step_number in range(1, max_steps + 1):
        active = np.flatnonzero(alive)
        if active.size == 0:
            break

        steps_used = step_number
        u = np.maximum(rng.random(active.size), np.finfo(float).tiny)
        step_length = -np.log(u) / mu_t_per_mm

        direction_z = uz[active]
        to_boundary = np.full(active.size, np.inf, dtype=np.float64)
        moving_down = direction_z > 1e-14
        moving_up = direction_z < -1e-14
        to_boundary[moving_down] = (
            thickness_mm - z[active[moving_down]]
        ) / direction_z[moving_down]
        to_boundary[moving_up] = (
            0.0 - z[active[moving_up]]
        ) / direction_z[moving_up]

        exits = step_length >= to_boundary
        if np.any(exits):
            exit_ids = active[exits]
            exit_directions = uz[exit_ids]
            n_transmitted += int(np.count_nonzero(exit_directions > 0.0))
            n_reflected += int(np.count_nonzero(exit_directions < 0.0))
            alive[exit_ids] = False

        interacts = ~exits
        if not np.any(interacts):
            continue

        interaction_ids = active[interacts]
        z[interaction_ids] += uz[interaction_ids] * step_length[interacts]
        is_absorbed = rng.random(interaction_ids.size) < (
            mu_a_per_mm / mu_t_per_mm
        )

        if np.any(is_absorbed):
            absorbed_ids = interaction_ids[is_absorbed]
            n_absorbed += absorbed_ids.size
            bin_ids = np.searchsorted(
                edges, z[absorbed_ids], side="right"
            ) - 1
            bin_ids = np.clip(bin_ids, 0, depth_bins - 1)
            absorbed_by_depth += np.bincount(
                bin_ids, minlength=depth_bins
            )
            alive[absorbed_ids] = False

        scatter_ids = interaction_ids[~is_absorbed]
        if scatter_ids.size == 0:
            continue

        cos_theta, phi = _sample_henyey_greenstein(rng, g, scatter_ids.size)
        sin_theta = np.sqrt(np.maximum(0.0, 1.0 - cos_theta * cos_theta))
        old_uz = uz[scatter_ids]
        radial_component = np.sqrt(np.maximum(0.0, 1.0 - old_uz * old_uz))
        uz[scatter_ids] = np.clip(
            old_uz * cos_theta
            + radial_component * sin_theta * np.cos(phi),
            -1.0,
            1.0,
        )

    unfinished = int(np.count_nonzero(alive))
    inverse_n = 1.0 / num_photons
    transmitted_fraction = n_transmitted * inverse_n

    return Result(
        absorbed=n_absorbed * inverse_n,
        reflected=n_reflected * inverse_n,
        transmitted=transmitted_fraction,
        unfinished=unfinished * inverse_n,
        depth_edges_mm=edges,
        absorbed_by_depth=absorbed_by_depth * inverse_n,
        transmission_standard_error=float(
            np.sqrt(
                transmitted_fraction * (1.0 - transmitted_fraction)
                / num_photons
            )
        ),
        steps_used=steps_used,
    )


def beer_lambert_transmission(mu_a_per_mm: float, thickness_mm: float) -> float:
    """Transmisi untuk validasi khusus tanpa hamburan dan tanpa pantulan."""
    return float(np.exp(-mu_a_per_mm * thickness_mm))
