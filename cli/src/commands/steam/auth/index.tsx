import steamAuthLoginCommand, {
  steamAuthLoginAction,
} from '@/src/commands/steam/auth/login'
import steamAuthLogoutCommand, {
  steamAuthLogoutAction,
} from '@/src/commands/steam/auth/logout'
import steamAuthShowCommand, { steamAuthShowAction } from '@/src/commands/steam/auth/show'
import { AtlantisCommand } from '@/src/lib/command'
import { ensureNotCancelled } from '@/src/lib/prompts'
import * as p from '@clack/prompts'

export const steamAuthAction = async () => {
  const choice = ensureNotCancelled(
    await p.select({
      message: 'Select an authentication option',
      options: [
        { value: 'show', label: 'Show current account' },
        { value: 'login', label: 'Log in' },
        { value: 'logout', label: 'Log out' },
      ],
    })
  )

  switch (choice) {
    case 'show':
      await steamAuthShowAction()
      break

    case 'login':
      await steamAuthLoginAction()
      break

    case 'logout':
      await steamAuthLogoutAction()
      break

    default:
      break
  }
}

const steamAuthCommand = new AtlantisCommand('auth')
  .description('Authenticate with Steam')
  .action(steamAuthAction)
  .addCommand(steamAuthShowCommand)
  .addCommand(steamAuthLoginCommand)
  .addCommand(steamAuthLogoutCommand)

export default steamAuthCommand
