# Effect-TS Testing Patterns

Comprehensive testing patterns for Effect-TS services, errors, layers, and effects. Use this skill when writing tests for Effect-based code.

## Core Testing Setup

### @effect/vitest Integration

```typescript
import { describe, it, expect } from "@effect/vitest"
import { Effect } from "effect"

// Basic test - it.effect provides TestContext automatically
it.effect("test name", () =>
  Effect.gen(function* () {
    const result = yield* someEffect
    expect(result).toBe(expected)
  })
)

// Test with layers - provide dependencies to all tests
it.layer(MyServiceLive)("test with service", () =>
  Effect.gen(function* () {
    const service = yield* MyService
    const result = yield* service.doSomething()
    expect(result).toBe(expected)
  })
)

// Scoped tests - automatically handles resource cleanup
it.scoped("test with resources", () =>
  Effect.gen(function* () {
    const resource = yield* acquireResource
    // resource automatically released after test
    yield* useResource(resource)
  })
)
```

**Key Features:**
- `it.effect` - automatic TestContext provision (TestClock, TestRandom, etc.)
- `it.layer` - provide layers to test suite, shared across tests
- `it.scoped` - automatic resource cleanup
- Full fiber dumps with causes, spans, and logs for better errors

## Testing Services

### Mock Service with Layer.succeed

```typescript
import { Effect, Context, Layer } from "effect"

// Service definition
class DatabaseService extends Context.Tag("DatabaseService")<
  DatabaseService,
  {
    readonly query: (sql: string) => Effect.Effect<unknown>
  }
>() {}

// Live implementation (production)
export const DatabaseServiceLive = Layer.succeed(
  DatabaseService,
  {
    query: (sql) => Effect.promise(() => realDatabase.query(sql))
  }
)

// Test implementation (mocked)
export const DatabaseServiceTest = Layer.succeed(
  DatabaseService,
  {
    query: (sql) => Effect.succeed({ rows: [{ id: 1, name: "test" }] })
  }
)

// Usage in test
it.layer(DatabaseServiceTest)("queries database", () =>
  Effect.gen(function* () {
    const db = yield* DatabaseService
    const result = yield* db.query("SELECT * FROM users")
    expect(result).toEqual({ rows: [{ id: 1, name: "test" }] })
  })
)
```

**Convention:** Use "Live" suffix for production, "Test" suffix for mocks.

### Mock Service with Layer.mock

```typescript
import { Layer } from "effect"

// Partial mock - only implement methods you need
const PartialDatabaseMock = Layer.mock(DatabaseService, {
  query: (sql) => Effect.succeed({ rows: [] })
  // Other methods throw UnimplementedError when called
})

// Full mock with test doubles
const MockWithSpy = Layer.succeed(DatabaseService, {
  query: vi.fn().mockReturnValue(Effect.succeed({ rows: [] }))
})
```

### Testing Services with Dependencies

```typescript
class UserService extends Context.Tag("UserService")<
  UserService,
  {
    readonly getUser: (id: number) => Effect.Effect<User, UserNotFound>
  }
>() {}

class EmailService extends Context.Tag("EmailService")<
  EmailService,
  {
    readonly sendEmail: (to: string, body: string) => Effect.Effect<void>
  }
>() {}

// Service that depends on other services
class NotificationService extends Context.Tag("NotificationService")<
  NotificationService,
  {
    readonly notifyUser: (userId: number) => Effect.Effect<void, UserNotFound>
  }
>() {
  static Live = Layer.effect(
    NotificationService,
    Effect.gen(function* () {
      const users = yield* UserService
      const email = yield* EmailService

      return {
        notifyUser: (userId) =>
          Effect.gen(function* () {
            const user = yield* users.getUser(userId)
            yield* email.sendEmail(user.email, "Notification")
          })
      }
    })
  )
}

// Test with all dependencies mocked
const TestLayer = Layer.mergeAll(
  UserServiceTest,
  EmailServiceTest
).pipe(Layer.provideMerge(NotificationService.Live))

it.layer(TestLayer)("sends notification", () =>
  Effect.gen(function* () {
    const notif = yield* NotificationService
    yield* notif.notifyUser(1)
    // Verify email was sent using mocked EmailService
  })
)
```

## Testing Errors

### Expected Error Testing

```typescript
import { Effect, Exit } from "effect"

class MyError extends Data.TaggedError("MyError")<{
  readonly message: string
}> {}

it.effect("handles expected errors", () =>
  Effect.gen(function* () {
    const result = yield* Effect.exit(
      Effect.fail(new MyError({ message: "test error" }))
    )

    // Check error occurred
    expect(Exit.isFailure(result)).toBe(true)

    // Check error type
    if (Exit.isFailure(result)) {
      const cause = result.cause
      expect(Cause.isFailType(cause)).toBe(true)

      // Extract error value
      const error = Cause.failureOption(cause)
      expect(error).toBeSome()
      expect(Option.getOrThrow(error)).toBeInstanceOf(MyError)
    }
  })
)

// Alternative: use catchTag to verify error
it.effect("catches specific error type", () =>
  Effect.gen(function* () {
    let caught = false

    yield* effectThatFails.pipe(
      Effect.catchTag("MyError", (error) =>
        Effect.sync(() => {
          caught = true
          expect(error.message).toBe("test error")
        })
      )
    )

    expect(caught).toBe(true)
  })
)
```

### Multiple Error Types

```typescript
type UserServiceError = UserNotFound | DatabaseError | ValidationError

it.effect("handles multiple error types", () =>
  Effect.gen(function* () {
    const result = yield* Effect.either(service.getUser(999))

    expect(Either.isLeft(result)).toBe(true)

    if (Either.isLeft(result)) {
      // Pattern match on error type
      const error = result.left
      if (error._tag === "UserNotFound") {
        expect(error.userId).toBe(999)
      }
    }
  })
)
```

### Defect Testing (Unexpected Errors)

```typescript
it.effect("handles unexpected errors (defects)", () =>
  Effect.gen(function* () {
    const result = yield* Effect.exit(
      Effect.die(new Error("Unexpected"))
    )

    expect(Exit.isFailure(result)).toBe(true)

    if (Exit.isFailure(result)) {
      expect(Cause.isDie(result.cause)).toBe(true)
    }
  })
)
```

## Testing with TestClock

```typescript
import { TestClock } from "effect"

it.effect("delays execution", () =>
  Effect.gen(function* () {
    let executed = false

    // Fork effect that delays 1 second
    const fiber = yield* Effect.fork(
      Effect.delay("1 second")(
        Effect.sync(() => { executed = true })
      )
    )

    // Verify not executed yet
    expect(executed).toBe(false)

    // Advance time by 1 second
    yield* TestClock.adjust("1 second")

    // Wait for fiber to complete
    yield* Fiber.join(fiber)

    // Verify executed after time advance
    expect(executed).toBe(true)
  })
)

// Testing intervals
it.effect("processes scheduled tasks", () =>
  Effect.gen(function* () {
    const results: number[] = []

    const fiber = yield* Effect.fork(
      Effect.repeat(
        Effect.sync(() => results.push(Date.now())),
        Schedule.spaced("100 millis")
      ).pipe(Effect.timeout("1 second"))
    )

    // Advance time in increments
    yield* TestClock.adjust("100 millis")
    yield* TestClock.adjust("100 millis")
    yield* TestClock.adjust("100 millis")

    yield* Fiber.join(fiber)

    expect(results.length).toBeGreaterThan(0)
  })
)
```

## Testing with TestRandom

```typescript
import { TestRandom } from "effect"

it.effect("deterministic random values", () =>
  Effect.gen(function* () {
    // Set fixed random seed for reproducibility
    yield* TestRandom.setSeed(42)

    const random1 = yield* Random.next
    const random2 = yield* Random.next

    // Reset seed - same values again
    yield* TestRandom.setSeed(42)
    const random3 = yield* Random.next

    expect(random3).toBe(random1)
  })
)
```

## Testing Layers

### Fresh Layers Per Test

```typescript
// Helper to create fresh layer for each test
const makeFreshLayer = () =>
  Layer.succeed(MyService, {
    state: { counter: 0 }, // Fresh state per test
    increment: function() {
      this.state.counter++
      return Effect.succeed(this.state.counter)
    }
  })

describe("isolated tests", () => {
  it.effect("test 1", () =>
    Effect.gen(function* () {
      const service = yield* MyService
      const result = yield* service.increment()
      expect(result).toBe(1) // Fresh state
    }).pipe(Effect.provide(makeFreshLayer()))
  )

  it.effect("test 2", () =>
    Effect.gen(function* () {
      const service = yield* MyService
      const result = yield* service.increment()
      expect(result).toBe(1) // Fresh state again
    }).pipe(Effect.provide(makeFreshLayer()))
  )
})
```

### Layer Composition Testing

```typescript
// Test layer dependencies are wired correctly
it.effect("layer composition", () =>
  Effect.gen(function* () {
    // This test verifies all dependencies resolve
    const service = yield* TopLevelService
    const result = yield* service.operation()
    expect(result).toBeDefined()
  }).pipe(
    Effect.provide(
      TopLevelService.Live.pipe(
        Layer.provide(MiddleService.Live),
        Layer.provide(BottomService.Live)
      )
    )
  )
)
```

## Testing ConfigProvider

```typescript
import { ConfigProvider, Layer } from "effect"

// Mock config for tests
const TestConfig = Layer.setConfigProvider(
  ConfigProvider.fromMap(
    new Map([
      ["API_KEY", "test-key"],
      ["DATABASE_URL", "postgres://test"],
      ["PORT", "3000"]
    ])
  )
)

it.layer(TestConfig)("uses test configuration", () =>
  Effect.gen(function* () {
    const apiKey = yield* Config.string("API_KEY")
    expect(apiKey).toBe("test-key")
  })
)
```

## Testing HTTP Clients

```typescript
import { FetchHttpClient, HttpClient } from "@effect/platform"

// Mock fetch for testing
const MockFetch = Layer.succeed(
  FetchHttpClient.Fetch,
  () => Promise.resolve(
    new Response(JSON.stringify({ data: "test" }), {
      status: 200,
      headers: { "content-type": "application/json" }
    })
  )
)

it.layer(MockFetch)("makes HTTP request", () =>
  Effect.gen(function* () {
    const client = yield* HttpClient.HttpClient
    const response = yield* client.get("https://api.example.com/data")
    const json = yield* response.json
    expect(json).toEqual({ data: "test" })
  })
)
```

## Testing Concurrent Effects

```typescript
it.effect("race condition handling", () =>
  Effect.gen(function* () {
    const ref = yield* Ref.make(0)

    // Run 100 concurrent increments
    yield* Effect.all(
      Array.from({ length: 100 }, () =>
        Ref.update(ref, (n) => n + 1)
      ),
      { concurrency: "unbounded" }
    )

    const final = yield* Ref.get(ref)
    expect(final).toBe(100) // Ref is atomic
  })
)

it.effect("parallel execution", () =>
  Effect.gen(function* () {
    const fiber1 = yield* Effect.fork(longRunningTask1)
    const fiber2 = yield* Effect.fork(longRunningTask2)

    const [result1, result2] = yield* Effect.all([
      Fiber.join(fiber1),
      Fiber.join(fiber2)
    ])

    expect(result1).toBeDefined()
    expect(result2).toBeDefined()
  })
)
```

## Testing Streams

```typescript
import { Stream, Chunk } from "effect"

it.effect("stream processing", () =>
  Effect.gen(function* () {
    const stream = Stream.range(1, 5)
    const result = yield* Stream.runCollect(
      stream.pipe(Stream.map((n) => n * 2))
    )

    expect(Chunk.toArray(result)).toEqual([2, 4, 6, 8, 10])
  })
)

it.effect("stream error handling", () =>
  Effect.gen(function* () {
    const stream = Stream.range(1, 10).pipe(
      Stream.map((n) =>
        n === 5 ? Effect.fail("error") : Effect.succeed(n)
      ),
      Stream.flatMap(identity)
    )

    const result = yield* Effect.exit(Stream.runCollect(stream))
    expect(Exit.isFailure(result)).toBe(true)
  })
)
```

## Testing Effect.runPromise

```typescript
// For integrating with Promise-based test frameworks
describe("promise integration", () => {
  it("converts effect to promise", async () => {
    const effect = Effect.succeed(42)
    const result = await Effect.runPromise(effect)
    expect(result).toBe(42)
  })

  it("rejects on failure", async () => {
    const effect = Effect.fail(new MyError({ message: "fail" }))

    await expect(Effect.runPromise(effect)).rejects.toThrow()
  })

  it("provides dependencies for promise", async () => {
    const effect = Effect.gen(function* () {
      const service = yield* MyService
      return yield* service.doSomething()
    })

    const result = await Effect.runPromise(
      effect.pipe(Effect.provide(MyServiceTest))
    )

    expect(result).toBeDefined()
  })
})
```

## Best Practices

### 1. Use Descriptive Test Names

```typescript
// Good
it.effect("returns user when found in database", () => ...)
it.effect("fails with UserNotFound when user does not exist", () => ...)

// Bad
it.effect("test 1", () => ...)
it.effect("works", () => ...)
```

### 2. Test Happy Path and Error Cases

```typescript
describe("UserService.getUser", () => {
  it.effect("returns user when exists", () => ...)
  it.effect("fails with UserNotFound when not exists", () => ...)
  it.effect("fails with DatabaseError on connection failure", () => ...)
})
```

### 3. Keep Tests Isolated

```typescript
// Good - each test gets fresh state
it.effect("test 1", () =>
  Effect.provide(effect, makeFreshLayer())
)

// Bad - shared state between tests
const sharedLayer = makeLayer()
it.layer(sharedLayer)("test 1", () => ...)
it.layer(sharedLayer)("test 2", () => ...) // May see state from test 1
```

### 4. Use TestClock for Time-Based Tests

```typescript
// Good - instant, deterministic
it.effect("delays 1 hour", () =>
  Effect.gen(function* () {
    const fiber = yield* Effect.fork(Effect.delay("1 hour")(task))
    yield* TestClock.adjust("1 hour")
    yield* Fiber.join(fiber)
  })
)

// Bad - actually waits 1 hour
it.effect("delays 1 hour", () =>
  Effect.delay("1 hour")(task)
)
```

### 5. Mock External Dependencies

```typescript
// Good - all external services mocked
const TestLayer = Layer.mergeAll(
  DatabaseServiceTest,
  EmailServiceTest,
  PaymentServiceTest
)

// Bad - tests hit real services (slow, flaky, expensive)
const TestLayer = Layer.mergeAll(
  DatabaseServiceLive, // ❌ Real DB
  EmailServiceLive,    // ❌ Sends real emails
  PaymentServiceLive   // ❌ Charges real money
)
```

### 6. Test Error Propagation

```typescript
it.effect("propagates errors through effect chain", () =>
  Effect.gen(function* () {
    const result = yield* Effect.exit(
      service.getUser(999).pipe(
        Effect.flatMap((user) => service.processUser(user)),
        Effect.flatMap((processed) => service.saveUser(processed))
      )
    )

    // Verify UserNotFound from getUser propagated through chain
    expect(Exit.isFailure(result)).toBe(true)
  })
)
```

### 7. Use it.scoped for Resource Management

```typescript
// Good - automatic cleanup
it.scoped("uses database connection", () =>
  Effect.gen(function* () {
    const conn = yield* acquireConnection // Scope manages lifecycle
    yield* useConnection(conn)
    // Connection automatically closed after test
  })
)

// Bad - manual cleanup (easy to forget)
it.effect("uses database connection", () =>
  Effect.gen(function* () {
    const conn = yield* acquireConnection
    try {
      yield* useConnection(conn)
    } finally {
      yield* releaseConnection(conn)
    }
  })
)
```

## Common Patterns

### Testing Retry Logic

```typescript
it.effect("retries on failure", () =>
  Effect.gen(function* () {
    let attempts = 0

    const effect = Effect.gen(function* () {
      attempts++
      if (attempts < 3) {
        yield* Effect.fail("retry me")
      }
      return "success"
    }).pipe(
      Effect.retry(Schedule.recurs(5))
    )

    const result = yield* effect
    expect(result).toBe("success")
    expect(attempts).toBe(3)
  })
)
```

### Testing Timeouts

```typescript
it.effect("times out long operations", () =>
  Effect.gen(function* () {
    const longOp = Effect.delay("5 seconds")(Effect.succeed("done"))

    const result = yield* Effect.exit(
      longOp.pipe(Effect.timeout("1 second"))
    )

    expect(Exit.isFailure(result)).toBe(true)
    // Verify it's a TimeoutException
  }).pipe(Effect.provide(TestClock.layer))
)
```

### Testing Interruption

```typescript
it.effect("handles interruption gracefully", () =>
  Effect.gen(function* () {
    const ref = yield* Ref.make("initial")

    const fiber = yield* Effect.fork(
      Effect.gen(function* () {
        yield* Ref.set(ref, "started")
        yield* Effect.sleep("1 hour")
        yield* Ref.set(ref, "completed") // Should never reach here
      })
    )

    yield* TestClock.adjust("1 second")
    yield* Fiber.interrupt(fiber)

    const value = yield* Ref.get(ref)
    expect(value).toBe("started") // Not "completed"
  })
)
```

## Sources

- [Effect Official Documentation](https://effect.website/)
- [Effect Testing Documentation](https://effect.website/docs/testing/testclock/)
- [Effect-TS GitHub Repository](https://github.com/Effect-TS/effect)
- [Effect Solutions: Testing Guide](https://www.effect.solutions/testing)
- [Effect Patterns Repository](https://github.com/PaulJPhilp/EffectPatterns)
- [TypeOnce: Effect Testing Course](https://www.typeonce.dev/course/effect-beginners-complete-getting-started/testing-with-services/vitest-and-msw-testing-setup)
- [Running Effects Documentation](https://effect.website/docs/getting-started/running-effects/)
- [Managing Layers Documentation](https://effect.website/docs/requirements-management/layers/)
