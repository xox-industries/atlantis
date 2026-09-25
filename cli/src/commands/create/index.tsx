import createPalworldCommand, {
  createPalworldAction,
} from '@/src/commands/create/palworld'
import { AtlantisCommand } from '@/src/lib/command'
import { ensureNotCancelled } from '@/src/lib/prompts'
import * as p from '@clack/prompts'

const action = async () => {
  const choice = ensureNotCancelled(
    await p.select({
      message: 'Select a service to create',
      options: [{ value: 'palworld', label: 'Palworld (Windows)' }],
    })
  )

  if (choice === 'palworld') {
    await createPalworldAction()
  }
}

const createCommand = new AtlantisCommand('create')
  .description('Show creatable services')
  .action(action)
  .addCommand(createPalworldCommand)

export default createCommand
