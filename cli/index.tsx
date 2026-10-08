import completionCommand from '@/src/commands/completion'
import createCommand from '@/src/commands/create'
import startCommand from '@/src/commands/start'
import steamCommand from '@/src/commands/steam'
import stopCommand from '@/src/commands/stop'
import { AtlantisCommand } from '@/src/lib/command'
import { hyperlink } from '@/src/lib/strings'
import chalk from 'chalk'

const GITHUB_URL = 'https://github.com/xox-industries/atlantis'
const APP_VERSION = process.env.APP_VERSION || 'dev'

const program = new AtlantisCommand()
  .name('atlantis')
  .description(
    `${hyperlink(chalk.magentaBright('Atlantis'), GITHUB_URL)} is a centralized repository for managing and maintaining our Linux server infrastructure. ` +
      `${hyperlink(chalk.gray(`(${APP_VERSION})`), GITHUB_URL)}`
  )
  .addCommand(startCommand)
  .addCommand(stopCommand)
  .addCommand(createCommand)
  .addCommand(steamCommand)
  .addCommand(completionCommand)

const args = process.argv.slice(2)

if (args.length === 0) {
  program.help()
} else {
  program.parse()
}
