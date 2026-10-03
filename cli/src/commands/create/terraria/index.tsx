import createTerrariaCommand, {
  createTerrariaAction,
} from '@/src/commands/create/terraria/create'
import updateTerrariaCommand, {
  updateTerrariaAction,
} from '@/src/commands/create/terraria/update'
import { AtlantisCommand } from '@/src/lib/command'
import { ensureNotCancelled } from '@/src/lib/prompts'
import * as p from '@clack/prompts'

export { createTerrariaAction, updateTerrariaAction }

export const terrariaCommandAction = async () => {
  const choice = ensureNotCancelled(
    await p.select({
      message: 'Select an action for Terraria',
      options: [
        { value: 'create', label: 'Create a new manifest' },
        { value: 'update', label: 'Update an existing manifest' },
      ],
    })
  )

  if (choice === 'create') {
    await createTerrariaAction()
  } else {
    await updateTerrariaAction()
  }
}

const terrariaCommand = new AtlantisCommand('terraria')
  .description('Terraria options')
  .action(terrariaCommandAction)
  .addCommand(createTerrariaCommand)
  .addCommand(updateTerrariaCommand)

export default terrariaCommand
