import createTModLoaderCommand, {
  createTModLoaderAction,
} from '@/src/commands/create/tmodloader/create'
import updateTModLoaderCommand, {
  updateTModLoaderAction,
} from '@/src/commands/create/tmodloader/update'
import { AtlantisCommand } from '@/src/lib/command'
import { ensureNotCancelled } from '@/src/lib/prompts'
import * as p from '@clack/prompts'

export { createTModLoaderAction, updateTModLoaderAction }

export const tmodloaderCommandAction = async () => {
  const choice = ensureNotCancelled(
    await p.select({
      message: 'Select an action for TModLoader',
      options: [
        { value: 'create', label: 'Create a new manifest' },
        { value: 'update', label: 'Update an existing manifest' },
      ],
    })
  )

  if (choice === 'create') {
    await createTModLoaderAction()
  } else {
    await updateTModLoaderAction()
  }
}

const tmodloaderCommand = new AtlantisCommand('tmodloader')
  .description('TModLoader options')
  .action(tmodloaderCommandAction)
  .addCommand(createTModLoaderCommand)
  .addCommand(updateTModLoaderCommand)

export default tmodloaderCommand
