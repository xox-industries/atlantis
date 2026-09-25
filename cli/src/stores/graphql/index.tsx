import {
  ApolloClient,
  ApolloLink,
  FetchPolicy,
  InMemoryCache,
  OperationVariables,
} from '@apollo/client'
import { GraphQLWsLink } from '@apollo/client/link/subscriptions'
import { observableToAsyncIterable } from '@graphql-tools/utils'
import UploadHttpLink from 'apollo-upload-client/UploadHttpLink.mjs'
import { DocumentNode, Kind, OperationDefinitionNode } from 'graphql'
import { createClient as createWSClient } from 'graphql-ws'
import React, { useState } from 'react'
import { getSdk } from './generated'

const inMemoryCache = new InMemoryCache()

const createGraphQLClient = ({ endpoint }: { endpoint: string }) => {
  return getSdk(
    <R, V>(
      doc: DocumentNode,
      vars?: V,
      options?: { keepAlive?: number; fetchPolicy?: FetchPolicy }
    ) => {
      const definition = doc.definitions.find(
        (def): def is OperationDefinitionNode => def.kind === Kind.OPERATION_DEFINITION
      )

      switch (definition?.operation) {
        case 'query':
        case 'mutation': {
          return new Promise<R>((resolve, reject) => {
            ;(async () => {
              const client = new ApolloClient({
                cache: inMemoryCache,
                link: new UploadHttpLink({
                  uri: endpoint,
                }) as unknown as ApolloLink,
              })

              switch (definition?.operation) {
                case 'query': {
                  const { data, error } = await client.query<R>({
                    query: doc,
                    variables: vars as OperationVariables | undefined,
                    errorPolicy: 'all',
                    fetchPolicy: options?.fetchPolicy ?? 'no-cache',
                  })
                  if (error) {
                    return reject(error)
                  }
                  if (data == null) {
                    return reject(data)
                  }
                  return resolve(data)
                }

                case 'mutation': {
                  const { data, error } = await client.mutate<R>({
                    mutation: doc,
                    variables: vars as OperationVariables | undefined,
                    errorPolicy: 'all',
                  })
                  if (error) {
                    return reject(error)
                  }
                  if (data == null) {
                    return reject(data)
                  }
                  return resolve(data)
                }

                default:
                  throw new Error('Unsupported operation type')
              }
            })()
          })
        }

        case 'subscription': {
          return {
            [Symbol.asyncIterator](): AsyncIterator<R> {
              let initialized = false
              let iterator: AsyncIterator<R>

              return {
                next: async () => {
                  if (!initialized) {
                    initialized = true

                    const client = new ApolloClient({
                      cache: inMemoryCache,
                      link: new GraphQLWsLink(
                        createWSClient({
                          url: endpoint,
                          keepAlive: options?.keepAlive,
                        })
                      ),
                    })

                    const observable = client.subscribe<R>({
                      query: doc,
                      variables: vars as OperationVariables | undefined,
                      errorPolicy: 'all',
                      fetchPolicy: options?.fetchPolicy ?? 'no-cache',
                    })

                    const baseAsyncIterable =
                      observableToAsyncIterable<ApolloLink.Result<R>>(observable)

                    iterator = (async function* () {
                      for await (const result of baseAsyncIterable) {
                        if ('error' in result) {
                          throw result.error
                        }
                        if (result.errors) {
                          throw result.errors
                        }
                        yield result.data as R
                      }
                    })()
                  }

                  return iterator.next()
                },
              }
            },
          }
        }

        default:
          throw new Error('Unsupported operation type')
      }
    }
  )
}

export const graphQLClient = createGraphQLClient({
  endpoint: process.env.API_ENDPOINT_URL!,
})

const graphQLContext = React.createContext(
  undefined! as ReturnType<typeof createGraphQLClient>
)

export const Provider: React.FC<React.PropsWithChildren> = (props) => {
  const [state] = useState<ReturnType<typeof createGraphQLClient>>(
    createGraphQLClient({
      endpoint: process.env.API_ENDPOINT_URL!,
    })
  )

  return <graphQLContext.Provider value={state}>{props.children}</graphQLContext.Provider>
}

export const useGraphQLClient = () => {
  return React.useContext(graphQLContext)
}
