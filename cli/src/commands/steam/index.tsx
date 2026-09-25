import steamAuthCommand, { steamAuthAction } from '@/src/commands/steam/auth'
import steamValidateCommand, { steamValidateAction } from '@/src/commands/steam/validate'
import { AtlantisCommand } from '@/src/lib/command'
import { ensureNotCancelled } from '@/src/lib/prompts'
import * as p from '@clack/prompts'

const action = async () => {
  const choice = ensureNotCancelled(
    await p.select({
      message: 'Select a Steam option',
      options: [
        { value: 'auth', label: 'Authenticate' },
        { value: 'validate', label: 'Validate application' },
      ],
    })
  )

  switch (choice) {
    case 'auth':
      await steamAuthAction()
      break

    case 'validate':
      await steamValidateAction()
      break

    default:
      break
  }
}

const steamCommand = new AtlantisCommand('steam')
  .description('Steam options')
  .action(action)
  .addCommand(steamAuthCommand)
  .addCommand(steamValidateCommand)

export default steamCommand
