export function createDeferredPromise<T = void>() {
  let resolve: (value: T) => void
  let reject: (reason?: unknown) => void
  const promise = new Promise<T>((res, rej) => {
    resolve = res
    reject = rej
  })

  return {
    promise,
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    reject: reject!,
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    resolve: resolve!
  }
}

export function id(length: number) {
  let result = ''
  const characters =
    'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
  const charactersLength = characters.length
  for (let i = 0; i < length; i++) {
    result += characters.charAt(Math.floor(Math.random() * charactersLength))
  }
  return result
}
