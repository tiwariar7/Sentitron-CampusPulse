/**
 * Formats a date/timestamp to Indian Standard Time (IST) date and time.
 * Handles both timezone-naive backend strings and standard ISO strings.
 */
export function formatToIST(dateInput: string | Date | undefined | null): string {
  if (!dateInput) return '';
  
  let date: Date;
  if (typeof dateInput === 'string') {
    // If the string doesn't specify any timezone, append '+05:30' (IST)
    const hasTimezone = /Z|[+-]\d{2}:?\d{2}$/.test(dateInput);
    if (!hasTimezone) {
      date = new Date(dateInput + "+05:30");
    } else {
      date = new Date(dateInput);
    }
  } else {
    date = dateInput;
  }
  
  if (isNaN(date.getTime())) {
    return '';
  }

  return date.toLocaleString('en-IN', {
    timeZone: 'Asia/Kolkata',
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true
  });
}

/**
 * Formats a date/timestamp to Indian Standard Time (IST) time only.
 */
export function formatTimeToIST(dateInput: string | Date | undefined | null): string {
  if (!dateInput) return '';
  
  let date: Date;
  if (typeof dateInput === 'string') {
    const hasTimezone = /Z|[+-]\d{2}:?\d{2}$/.test(dateInput);
    if (!hasTimezone) {
      date = new Date(dateInput + "+05:30");
    } else {
      date = new Date(dateInput);
    }
  } else {
    date = dateInput;
  }
  
  if (isNaN(date.getTime())) {
    return '';
  }

  return date.toLocaleTimeString('en-IN', {
    timeZone: 'Asia/Kolkata',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true
  });
}
