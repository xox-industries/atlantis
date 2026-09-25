import stopPalworldCommand, { stopPalworldAction } from '@/src/commands/stop/palworld'
import { AtlantisCommand } from '@/src/lib/command'
import { ensureNotCancelled } from '@/src/lib/prompts'
import * as p from '@clack/prompts'

const action = async () => {
  const choice = ensureNotCancelled(
    await p.select({
      message: 'Select a service to stop',
      options: [{ value: 'palworld', label: 'Palworld' }],
    })
  )

  if (choice === 'palworld') {
    await stopPalworldAction()
  }
}

const stopCommand = new AtlantisCommand('stop')
  .description('Show stoppable services')
  .action(action)
  .addCommand(stopPalworldCommand)

export default stopCommand
