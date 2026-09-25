import * as React from 'react'
import { Provider as GraphQLClientProvider } from './graphql'

const providers = [GraphQLClientProvider]

const Provider: React.FC<React.PropsWithChildren> = (props) => {
  return providers.reduceRight(
    (child, Provider) => <Provider>{child}</Provider>,
    <>{props.children}</>
  )
}

export default Provider
