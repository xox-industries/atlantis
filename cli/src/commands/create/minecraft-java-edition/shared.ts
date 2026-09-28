export type MinecraftModloaderType = 'forge' | 'fabric' | 'neoforge'

export const MODLOADER_OPTIONS: { value: MinecraftModloaderType; label: string }[] = [
  { value: 'neoforge', label: 'NeoForge' },
  { value: 'forge', label: 'Forge' },
  { value: 'fabric', label: 'Fabric' },
]
