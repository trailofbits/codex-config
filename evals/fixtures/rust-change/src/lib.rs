use std::fmt;

#[derive(Debug, PartialEq)]
pub struct RetryError(String);

impl fmt::Display for RetryError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(formatter, "{}", self.0)
    }
}

pub fn parse_retries(value: &str) -> Result<u8, RetryError> {
    value
        .parse::<u8>()
        .map_err(|_| RetryError(format!("invalid retry count: {value}")))
}

#[cfg(test)]
mod tests {
    use super::parse_retries;

    #[test]
    fn parses_retry_count() {
        assert_eq!(parse_retries("3"), Ok(3));
    }

    #[test]
    fn rejects_malformed_count() {
        assert!(parse_retries("many").is_err());
    }
}
