import * as p from '@clack/prompts'

export const ensureNotCancelled = <T>(value: T | typeof p.CANCEL_SYMBOL): T => {
  if (value === p.CANCEL_SYMBOL) {
    p.cancel('Cancelled')
    process.exit(1)
  }

  return value
}
