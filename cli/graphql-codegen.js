/** @type {import('@graphql-codegen/cli').CodegenConfig} */
const config = {
  overwrite: true,
  generates: {
    ['src/stores/graphql/generated.ts']: {
      schema: process.argv[4],
      documents: ['src/**/*.graphql'],
      plugins: [
        { typescript: { typesPrefix: 'Schema' } },
        { 'typescript-operations': { onlyOperationTypes: true } },
        'typescript-generic-sdk',
      ],
      config: {
        defaultScalarType: 'string',
        enumsAsTypes: true,
        gqlImport: 'graphql-tag#gql',
        useTypeImports: true,
      },
    },
  },
}

export default config
