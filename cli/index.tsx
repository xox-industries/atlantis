import createCommand from '@/src/commands/create'
import startCommand from '@/src/commands/start'
import { AtlantisCommand } from '@/src/lib/command'

const program = new AtlantisCommand()
  .name('atlantis')
  .description(
    'Atlantis is a centralized repository for managing and maintaining our Linux server infrastructure.'
  )
  .addCommand(createCommand)
  .addCommand(startCommand)

const args = process.argv.slice(2)

if (args.length === 0) {
  program.help()
} else {
  program.parse()
}
