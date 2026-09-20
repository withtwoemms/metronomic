use std::io::Read;

use clap::{Parser, Subcommand};
use rand::distr::weighted::WeightedIndex;
use rand::prelude::*;

/// Simulate noisy sensor timestamps and regularize them losslessly.
#[derive(Parser)]
#[command(name = "metronomic", version)]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Subcommand)]
enum Command {
    /// Emit timestamps jittered about multiples of PERIOD.
    Generate {
        /// Nominal period of sensor.
        #[arg(long)]
        period: i64,
        /// Number of timestamps to generate.
        #[arg(long, default_value_t = 20)]
        count: i64,
        /// Seed the RNG for reproducible output.
        #[arg(long)]
        seed: Option<u64>,
    },
    /// Fit noisy TIMESTAMPS (args or stdin) to a regular grid.
    ///
    /// Emits the grid (period, offset) plus per-timestamp residuals, from
    /// which the input reconstructs exactly -- no information is lost.
    Regularize {
        timestamps: Vec<String>,
    },
}

/// Modified Bessel function of the first kind, integer order, by series
/// expansion: I_n(x) = sum_k (x/2)^(n+2k) / (k! (n+k)!).
fn bessel_iv(order: i64, x: f64) -> f64 {
    let n = order.unsigned_abs() as u32; // I_{-n}(x) == I_n(x)
    let half = x / 2.0;
    let mut sum = 0.0;
    for k in 0..40 {
        sum += half.powi((n + 2 * k) as i32) / (factorial(k) * factorial(n + k));
    }
    sum
}

fn factorial(n: u32) -> f64 {
    (1..=n).map(f64::from).product()
}

/// Normalized discrete Gaussian kernel over integer offsets -spread..=spread.
fn discrete_gaussian_kernel(spread: i64, scale: f64) -> Vec<f64> {
    let weights: Vec<f64> = (-spread..=spread)
        .map(|j| (-scale).exp() * bessel_iv(j, scale))
        .collect();
    let total: f64 = weights.iter().sum();
    weights.iter().map(|w| w / total).collect()
}

/// Least-squares fit of timestamps to index -> offset + index * period,
/// rounded half-to-even to match the Python reference implementation.
fn estimate_grid(timestamps: &[i64]) -> (i64, i64) {
    let n = timestamps.len() as f64;
    let (mut si, mut st, mut sit, mut sii) = (0.0, 0.0, 0.0, 0.0);
    for (i, &t) in timestamps.iter().enumerate() {
        let (i, t) = (i as f64, t as f64);
        si += i;
        st += t;
        sit += i * t;
        sii += i * i;
    }
    let slope = (n * sit - si * st) / (n * sii - si * si);
    let intercept = (st - slope * si) / n;
    (
        slope.round_ties_even() as i64,
        intercept.round_ties_even() as i64,
    )
}

fn compute_residuals(timestamps: &[i64], period: i64, offset: i64) -> Vec<i64> {
    timestamps
        .iter()
        .enumerate()
        .map(|(i, &t)| t - (offset + i as i64 * period))
        .collect()
}

fn reconstruct(period: i64, offset: i64, residuals: &[i64]) -> Vec<i64> {
    residuals
        .iter()
        .enumerate()
        .map(|(i, &r)| offset + i as i64 * period + r)
        .collect()
}

/// Extract every integer (regex -?\d+ equivalent) from free-form text.
fn parse_timestamps(text: &str) -> Vec<i64> {
    let mut values = Vec::new();
    let bytes = text.as_bytes();
    let mut i = 0;
    while i < bytes.len() {
        if bytes[i].is_ascii_digit() || (bytes[i] == b'-' && bytes.get(i + 1).is_some_and(u8::is_ascii_digit)) {
            let start = i;
            i += 1;
            while i < bytes.len() && bytes[i].is_ascii_digit() {
                i += 1;
            }
            values.push(text[start..i].parse().unwrap());
        } else {
            i += 1;
        }
    }
    values
}

fn format_list(values: &[i64]) -> String {
    let items: Vec<String> = values.iter().map(|v| v.to_string()).collect();
    format!("[{}]", items.join(", "))
}

fn generate(period: i64, count: i64, seed: Option<u64>) {
    let spread = 3;
    let kernel = discrete_gaussian_kernel(spread, 1.0);
    let dist = WeightedIndex::new(&kernel).expect("kernel weights are positive");
    let mut rng = match seed {
        Some(seed) => StdRng::seed_from_u64(seed),
        None => StdRng::from_os_rng(),
    };
    let timestamps: Vec<i64> = (1..count)
        .map(|i| i * period - spread + dist.sample(&mut rng) as i64)
        .collect();
    println!("{}", format_list(&timestamps));
}

fn regularize(args: Vec<String>) {
    let text = if args.is_empty() {
        let mut buf = String::new();
        std::io::stdin()
            .read_to_string(&mut buf)
            .expect("failed to read stdin");
        buf
    } else {
        args.join(" ")
    };
    let values = parse_timestamps(&text);
    if values.len() < 2 {
        eprintln!("Error: Need at least two timestamps to fit a grid.");
        std::process::exit(2);
    }
    let (period, offset) = estimate_grid(&values);
    let residuals = compute_residuals(&values, period, offset);
    let lossless = reconstruct(period, offset, &residuals) == values;
    println!("period:    {period}");
    println!("offset:    {offset}");
    println!("residuals: {}", format_list(&residuals));
    println!("lossless:  {}", if lossless { "True" } else { "False" });
}

fn main() {
    match Cli::parse().command {
        Command::Generate { period, count, seed } => generate(period, count, seed),
        Command::Regularize { timestamps } => regularize(timestamps),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn kernel_matches_scipy_values() {
        // normalize(exp(-1) * iv([-3..3], 1)), cross-checked against scipy.special.iv
        let kernel = discrete_gaussian_kernel(3, 1.0);
        let expected = [0.00817355, 0.05005046, 0.20837538, 0.46680122];
        for (got, want) in kernel.iter().zip(expected) {
            assert!((got - want).abs() < 1e-8);
        }
        let total: f64 = kernel.iter().sum();
        assert!((total - 1.0).abs() < 1e-12);
        assert_eq!(kernel[0], kernel[6]); // symmetric
    }

    #[test]
    fn grid_estimation_rounds_ties_to_even() {
        // slope is exactly 2.5; Python's round() gives 2
        let (period, offset) = estimate_grid(&[0, 3, 5, 8, 10]);
        assert_eq!((period, offset), (2, 0));
    }

    #[test]
    fn regularization_is_lossless() {
        let values = vec![103, 199, 305, 397, 502];
        let (period, offset) = estimate_grid(&values);
        let residuals = compute_residuals(&values, period, offset);
        assert_eq!(reconstruct(period, offset, &residuals), values);
    }

    #[test]
    fn parses_integers_from_arbitrary_text() {
        assert_eq!(parse_timestamps("[10, -22, 30]\nx7"), vec![10, -22, 30, 7]);
    }
}
