import startPalworldCommand, { startPalworldAction } from '@/src/commands/start/palworld'
import { AtlantisCommand } from '@/src/lib/command'
import { ensureNotCancelled } from '@/src/lib/prompts'
import * as p from '@clack/prompts'

const action = async () => {
  const choice = ensureNotCancelled(
    await p.select({
      message: 'Select a service to start',
      options: [{ value: 'palworld', label: `Palworld (Windows)` }],
    })
  )

  if (choice === 'palworld') {
    await startPalworldAction()
  }
}

const startCommand = new AtlantisCommand('start')
  .description('Show startable services')
  .action(action)
  .addCommand(startPalworldCommand)

export default startCommand
