# Test Doubles Architecture for TDD DSL

> **Status:** Design Document  
> **Scope:** Post-MVP Major Feature  
> **Related:** Mountebank-inspired stub server capabilities, multi-language test double generation

---

## Executive Summary

This document proposes a major architectural upgrade to tdd-dsl: **test double generation**. Beyond generating test scaffolding, tdd-dsl would generate test doubles (mocks, stubs, spies) alongside tests, enabling contract-first development of external dependencies.

Drawing inspiration from [Mountebank](http://www.mbtest.org/)'s stub server architecture and combining it with per-language test double patterns, this feature would enable:

- **HTTP stub server generation** for integration testing
- **Function/class mocking** for unit testing per language
- **Spy/verification patterns** for interaction testing
- **Contract validation** between services

---

## Table of Contents

1. [Overview of Test Double Types](#1-overview-of-test-double-types)
2. [Mountebank Inspiration](#2-mountebank-inspiration)
3. [DSL Syntax Extensions](#3-dsl-syntax-extensions)
4. [Per-Language Implementation](#4-per-language-implementation)
5. [Server Mode vs Inline Generation](#5-server-mode-vs-inline-generation)
6. [Contract Validation](#6-contract-validation)
7. [Integration with Existing Emitters](#7-integration-with-existing-emitters)
8. [Implementation Roadmap](#8-implementation-roadmap)
9. [Risk Assessment](#9-risk-assessment)

---

## 1. Overview of Test Double Types

### 1.1 Taxonomy

| Type | Purpose | Use Case |
|------|---------|----------|
| **Stub** | Provides canned answers | Return hardcoded responses for specific inputs |
| **Mock** | Expects specific calls | Verify interactions happened as expected |
| **Spy** | Records calls for later verification | Inspect what was called without pre-configuring |
| **Fake** | Working implementation (simplified) | In-memory database, lightweight HTTP server |
| **Dummy** | Placeholder (not used) | Fill parameter lists |

### 1.2 Cross-Language Patterns

The challenge: what patterns work across all 10 supported languages?

| Pattern | Python | TypeScript | Java | C# | Rust | Go | Odin | Zig |
|---------|--------|------------|------|-----|------|-----|------|-----|
| **Stub Function** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Mock Object** | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| **Spy Function** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **HTTP Stub Server** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Interface Mocking** | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| **Callback Stubbing** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

**Legend:** ✅ = Natural fit, ⚠️ = Requires patterns

### 1.3 Universal Patterns

The following patterns work well across all languages:

1. **HTTP Stub Servers** - Language-agnostic via HTTP protocol
2. **Function Stubs** - Direct function replacement
3. **Callback/Closure Stubs** - Passing test doubles as arguments
4. **Spy via Wrapper** - Record calls then delegate

---

## 2. Mountebank Inspiration

### 2.1 Core Mountebank Concepts

Mountebank is a cross-platform, multi-protocol test double tool. Key concepts:

#### Imposters
An imposter represents a test double listening on a specific port:

```json
{
  "port": 4545,
  "protocol": "http",
  "stubs": [...],
  "name": "Payment Service"
}
```

#### Stubs
A stub defines request-response pairs:

```json
{
  "predicates": [...],
  "responses": [...]
}
```

#### Predicates
Predicates match incoming requests:

```json
{
  "equals": {
    "method": "POST",
    "path": "/api/payments",
    "body": { "amount": 100 }
  }
}
```

#### Responses
Responses define what to return:

```json
{
  "is": {
    "statusCode": 200,
    "body": { "id": "pay_123", "status": "approved" }
  }
}
```

### 2.2 TDD DSL Adaptation

We adapt these concepts to the DSL:

| Mountebank | TDD DSL Equivalent |
|------------|-------------------|
| Imposter | `mock server` block |
| Stub | `stub` block within server |
| Predicate | `when` conditions in stub |
| Response | `then return` in stub |
| Name | `as` identifier |

---

## 3. DSL Syntax Extensions

### 3.1 Core Syntax Proposal

#### Mock Server Declaration

```text
suite "Payment processing"
target python "payment_service"

mock server "payment_gateway" as gateway:
  port: 4545
  protocol: http

  stub "successful payment":
    when request:
      {
        "method": "POST",
        "path": "/api/charge",
        "body": {"amount": 100, "currency": "USD"}
      }
    then return:
      {
        "status": 200,
        "body": {"id": "ch_123", "status": "succeeded"}
      }

  stub "insufficient funds":
    when request:
      {"method": "POST", "path": "/api/charge", "body": {"amount": 99999}}
    then return:
      {
        "status": 402,
        "body": {"error": "insufficient_funds", "decline_code": "card_declined"}
      }

case "processes valid payment":
  given input:
    {"amount": 100, "gateway_url": "http://localhost:4545"}
  when call "process_payment"
  then equals:
    {"success": true, "transaction_id": "ch_123"}
```

#### Function Mock Declaration

```text
mock function "get_user_by_id" as fetch_user:
  when called with:
    [{"id": 1}]
  then return:
    {"id": 1, "name": "Alice", "active": true}

  when called with:
    [{"id": 999}]
  then throw:
    "UserNotFoundError"

case "greets active user":
  given mocks:
    [fetch_user]
  given input:
    {"user_id": 1}
  when call "greet_user"
  then equals:
    "Hello, Alice!"
```

#### Spy Declaration

```text
spy function "send_email" as email_spy

case "sends welcome email":
  given spies:
    [email_spy]
  given input:
    {"user": {"email": "alice@example.com", "name": "Alice"}}
  when call "register_user"
  then equals:
    {"registered": true}
  then spy email_spy was called:
    {"to": "alice@example.com", "template": "welcome"}
```

### 3.2 Extended Grammar

```text
document      = suite target* mock* case+

mock          = mock-server | mock-function | spy-function

mock-server   = "mock server" quoted "as" identifier ":" server-config stub+
server-config = ("port:" number)? ("protocol:" (http|https|tcp))?
stub          = "stub" quoted ":" when-request then-return
when-request  = indent "when request:" json-block
then-return   = indent "then return:" json-block

mock-function = "mock function" quoted "as" identifier ":" mock-case+
mock-case     = "when called with:" json-block ("then return:" json-block | "then throw:" quoted)

spy-function  = "spy function" quoted "as" identifier
spy-verify    = "then spy" identifier "was called:" json-block
                | "then spy" identifier "was called" number "times"
                | "then spy" identifier "was not called"

case          = "case" quoted ":" case-step+
case-step     = given-mocks | given-spies | given-input | when-call | then-equals | spy-verify
given-mocks   = indent "given mocks:" json-array
given-spies   = indent "given spies:" json-array
```

### 3.3 Configuration Options

```text
mock server "auth_service" as auth:
  port: 8080
  protocol: http
  
  # Optional: Auto-start configuration
  lifecycle: test  # test | suite | manual
  
  # Optional: Response delays
  default_delay_ms: 100
  
  # Optional: Match behavior
  match_strategy: first  # first | combine
```

---

## 4. Per-Language Implementation

### 4.1 Python Implementation

**Libraries:** `unittest.mock`, `responses` (HTTP), `pytest-httpserver`

```python
# Generated from mock function
from unittest.mock import MagicMock

fetch_user = MagicMock()
fetch_user.side_effect = [
    {"id": 1, "name": "Alice", "active": True},  # First call
    Exception("UserNotFoundError"),                # Second call
]

# Generated from mock server
import responses

@responses.activate
def test_processes_valid_payment():
    responses.post(
        "http://localhost:4545/api/charge",
        json={"id": "ch_123", "status": "succeeded"},
        status=200,
        match=[
            responses.json_params_matcher({"amount": 100, "currency": "USD"})
        ]
    )
    
    result = payment_service.process_payment(
        amount=100, 
        gateway_url="http://localhost:4545"
    )
    assert result == {"success": True, "transaction_id": "ch_123"}

# Generated from spy
email_spy = MagicMock()

def test_sends_welcome_email():
    with patch('module.send_email', email_spy):
        result = register_user({"user": {"email": "alice@example.com", "name": "Alice"}})
        
    assert result == {"registered": True}
    email_spy.assert_called_once_with(
        to="alice@example.com",
        template="welcome"
    )
```

### 4.2 TypeScript Implementation

**Libraries:** `vitest` (built-in mocking), `msw` (HTTP mocking)

```typescript
// Generated from mock function
import { vi } from 'vitest';

const fetch_user = vi.fn();
fetch_user
  .mockReturnValueOnce({id: 1, name: "Alice", active: true})
  .mockRejectedValueOnce(new Error("UserNotFoundError"));

// Generated from mock server
import { rest } from 'msw';
import { setupServer } from 'msw/node';

const gateway_server = setupServer(
  rest.post('http://localhost:4545/api/charge', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({id: "ch_123", status: "succeeded"})
    );
  })
);

beforeAll(() => gateway_server.listen());
afterEach(() => gateway_server.resetHandlers());
afterAll(() => gateway_server.close());

test("processes valid payment", () => {
  const result = process_payment({amount: 100, gateway_url: "http://localhost:4545"});
  expect(result).toEqual({success: true, transaction_id: "ch_123"});
});

// Generated from spy
const email_spy = vi.fn();

test("sends welcome email", () => {
  vi.mocked(send_email).mockImplementation(email_spy);
  
  const result = register_user({user: {email: "alice@example.com", name: "Alice"}});
  
  expect(result).toEqual({registered: true});
  expect(email_spy).toHaveBeenCalledWith({
    to: "alice@example.com",
    template: "welcome"
  });
});
```

### 4.3 Java Implementation

**Libraries:** `Mockito`, `WireMock` (HTTP)

```java
// Generated from mock function
import static org.mockito.Mockito.*;

UserService fetch_user = mock(UserService.class);
when(fetch_user.getUserById(argThat(id -> id == 1)))
  .thenReturn(new User(1, "Alice", true));
when(fetch_user.getUserById(argThat(id -> id == 999)))
  .thenThrow(new UserNotFoundError());

// Generated from mock server
import com.github.tomakehurst.wiremock.WireMockServer;
import static com.github.tomakehurst.wiremock.client.WireMock.*;

WireMockServer gatewayServer = new WireMockServer(4545);

gatewayServer.stubFor(post(urlEqualTo("/api/charge"))
  .withRequestBody(equalToJson("{\"amount\": 100, \"currency\": \"USD\"}"))
  .willReturn(aResponse()
    .withStatus(200)
    .withBody("{\"id\": \"ch_123\", \"status\": \"succeeded\"}")));

@Test
@DisplayName("processes valid payment")
public void testProcessesValidPayment() {
    var input = Map.of("amount", 100, "gateway_url", "http://localhost:4545");
    var result = paymentService.processPayment(input);
    assertEquals(Map.of("success", true, "transaction_id", "ch_123"), result);
}

// Generated from spy
EmailService emailSpy = mock(EmailService.class);

@Test
@DisplayName("sends welcome email")
public void testSendsWelcomeEmail() {
    var input = Map.of("user", Map.of("email", "alice@example.com", "name", "Alice"));
    var result = registerUser(input);
    
    assertEquals(Map.of("registered", true), result);
    verify(emailSpy).sendEmail(argThat(email -> 
        email.to.equals("alice@example.com") && 
        email.template.equals("welcome")
    ));
}
```

### 4.4 C# Implementation

**Libraries:** `Moq`, `WireMock.Net`

```csharp
// Generated from mock function
var fetch_user = new Mock<IUserService>();
fetch_user.Setup(x => x.GetUserById(It.Is<int>(id => id == 1)))
  .Returns(new User { Id = 1, Name = "Alice", Active = true });
fetch_user.Setup(x => x.GetUserById(It.Is<int>(id => id == 999)))
  .Throws(new UserNotFoundException());

// Generated from mock server
using WireMock.Server;
using static WireMock.RequestBuilders.Request;
using static WireMock.ResponseBuilders.Response;

var gatewayServer = WireMockServer.Start(4545);
gatewayServer
  .Given(
    Request.Create()
      .WithPath("/api/charge")
      .WithBody(new JsonMatcher("{\"amount\": 100, \"currency\": \"USD\"}"))
  )
  .RespondWith(
    Response.Create()
      .WithStatusCode(200)
      .WithBody("{\"id\": \"ch_123\", \"status\": \"succeeded\"}")
  );

[Fact]
public void testProcessesValidPayment()
{
    var input = new Dictionary<string, object> { 
        ["amount"] = 100, 
        ["gateway_url"] = "http://localhost:4545" 
    };
    var result = paymentService.ProcessPayment(input);
    Assert.Equal(true, result["success"]);
}

// Generated from spy
var emailSpy = new Mock<IEmailService>();

[Fact]
public void testSendsWelcomeEmail()
{
    var input = new Dictionary<string, object> {
        ["user"] = new Dictionary<string, object> {
            ["email"] = "alice@example.com",
            ["name"] = "Alice"
        }
    };
    var result = registerUser(input);
    
    Assert.Equal(true, result["registered"]);
    emailSpy.Verify(x => x.SendEmail(It.Is<Email>(e => 
        e.To == "alice@example.com" && e.Template == "welcome"
    )), Times.Once);
}
```

### 4.5 Rust Implementation

**Libraries:** `mockall` (mocking), `wiremock` (HTTP), `tokio::test`

```rust
// Generated from mock function
use mockall::mock;

mock! {
    UserService {}
    impl UserService {
        fn get_user_by_id(&self, id: i64) -> Result<User, UserNotFoundError>;
    }
}

let mut fetch_user = MockUserService::new();
fetch_user
  .expect_get_user_by_id()
  .with(eq(1))
  .returning(|_| Ok(User { id: 1, name: "Alice".to_string(), active: true }));
fetch_user
  .expect_get_user_by_id()
  .with(eq(999))
  .returning(|_| Err(UserNotFoundError));

// Generated from mock server
use wiremock::{MockServer, Mock, ResponseTemplate};
use wiremock::matchers::{method, path, body_json};

let gateway_server = MockServer::start().await;

Mock::given(method("POST"))
  .and(path("/api/charge"))
  .and(body_json(json!({"amount": 100, "currency": "USD"})))
  .respond_with(ResponseTemplate::new(200)
    .set_body_json(json!({"id": "ch_123", "status": "succeeded"})))
  .mount(&gateway_server)
  .await;

#[tokio::test]
async fn test_processes_valid_payment() {
    let input = HashMap::from([
        ("amount", 100),
        ("gateway_url", gateway_server.uri()),
    ]);
    let result = payment_service::process_payment(&input).await;
    assert_eq!(result["success"], true);
}

// Generated from spy
use mockall::mock;

mock! {
    EmailService {}
    impl EmailService {
        fn send_email(&self, to: &str, template: &str);
    }
}

let email_spy = MockEmailService::new();
email_spy.expect_send_email()
  .with(eq("alice@example.com"), eq("welcome"))
  .times(1);
```

### 4.6 Go Implementation

**Libraries:** `gomock` or `testify/mock`, `gock` (HTTP)

```go
// Generated from mock function
import (
    "github.com/golang/mock/gomock"
)

ctrl := gomock.NewController(t)
defer ctrl.Finish()

mockUserService := NewMockUserService(ctrl)
mockUserService.EXPECT().
    GetUserById(int64(1)).
    Return(&User{Id: 1, Name: "Alice", Active: true}, nil)
mockUserService.EXPECT().
    GetUserById(int64(999)).
    Return(nil, ErrUserNotFound)

// Generated from mock server
import (
    "github.com/h2non/gock"
)

defer gock.Off()

gock.New("http://localhost:4545").
    Post("/api/charge").
    JSON(map[string]interface{}{"amount": 100, "currency": "USD"}).
    Reply(200).
    JSON(map[string]interface{}{"id": "ch_123", "status": "succeeded"})

func TestProcessesValidPayment(t *testing.T) {
    input := map[string]interface{}{
        "amount": 100,
        "gateway_url": "http://localhost:4545",
    }
    result := ProcessPayment(input)
    
    expected := map[string]interface{}{
        "success": true,
        "transaction_id": "ch_123",
    }
    if !reflect.DeepEqual(result, expected) {
        t.Errorf("expected %v, got %v", expected, result)
    }
}

// Generated from spy
type EmailSpy struct {
    Calls []EmailCall
}

type EmailCall struct {
    To       string
    Template string
}

func (s *EmailSpy) SendEmail(to, template string) {
    s.Calls = append(s.Calls, EmailCall{To: to, Template: template})
}

func TestSendsWelcomeEmail(t *testing.T) {
    emailSpy := &EmailSpy{}
    
    // Inject spy
    originalSend := sendEmailFunc
    sendEmailFunc = emailSpy.SendEmail
    defer func() { sendEmailFunc = originalSend }()
    
    input := map[string]interface{}{
        "user": map[string]interface{}{
            "email": "alice@example.com",
            "name":  "Alice",
        },
    }
    result := RegisterUser(input)
    
    if result["registered"] != true {
        t.Errorf("expected registration to succeed")
    }
    if len(emailSpy.Calls) != 1 {
        t.Errorf("expected 1 email call, got %d", len(emailSpy.Calls))
    }
    if emailSpy.Calls[0].To != "alice@example.com" {
        t.Errorf("expected email to alice@example.com")
    }
}
```

### 4.7 Odin Implementation

**Challenges:** Odin lacks mature mocking libraries. Use interface-based testing and manual stubs.

```odin
package payment_test

import "core:testing"

// Define interface for testability
UserFetcher :: interface {
    get_user_by_id: proc(id: i64) -> (User, bool),
}

// Manual stub implementation
TestUserFetcher :: struct {
    users: map[i64]User,
}

test_fetcher_get_user_by_id :: proc(tf: ^TestUserFetcher, id: i64) -> (User, bool) {
    user, ok := tf.users[id]
    return user, ok
}

// HTTP stub using test HTTP server
// (Odin's standard library has basic HTTP client, limited server support)

@(test)
test_processes_valid_payment :: proc(t: ^testing.T) {
    // Manual dependency injection
    fetcher := TestUserFetcher{
        users = {
            1 = {id = 1, name = "Alice", active = true},
        },
    }
    
    // For HTTP, spin up a simple test server or use localhost
    // This is where Odin would need external tooling or OS-level process spawning
    
    input := struct {
        amount: int,
        gateway_url: string,
    }{amount = 100, gateway_url = "http://localhost:4545"}
    
    result := process_payment(input, &fetcher)
    
    testing.expect_value(t, result.success, true)
    testing.expect_value(t, result.transaction_id, "ch_123")
}
```

### 4.8 Zig Implementation

**Challenges:** Zig is explicitly designed without traditional mocking. Use comptime and dependency injection.

```zig
const std = @import("std");

// Define interface via function pointers
const UserFetcher = struct {
    ctx: *anyopaque,
    get_user_by_id: *const fn (ctx: *anyopaque, id: i64) anyerror!User,
};

// Test stub implementation
const TestUserFetcher = struct {
    users: std.AutoHashMap(i64, User),
    
    fn getUserById(ctx: *anyopaque, id: i64) anyerror!User {
        const self = @ptrCast(*TestUserFetcher, @alignCast(ctx));
        return self.users.get(id) orelse error.UserNotFound;
    }
    
    fn toInterface(self: *TestUserFetcher) UserFetcher {
        return .{
            .ctx = self,
            .get_user_by_id = getUserById,
        };
    }
};

// For HTTP, use test server or mock at network level
// Zig's std.http is minimal; integration tests often use external processes

test "processes valid payment" {
    var fetcher = TestUserFetcher{
        .users = std.AutoHashMap(i64, User).init(testing.allocator),
    };
    defer fetcher.users.deinit();
    
    try fetcher.users.put(1, .{ .id = 1, .name = "Alice", .active = true });
    
    const input = .{
        .amount = 100,
        .gateway_url = "http://localhost:4545",
    };
    
    const result = try process_payment(input, fetcher.toInterface());
    try std.testing.expectEqual(true, result.success);
}
```

---

## 5. Server Mode vs Inline Generation

### 5.1 Server Mode

A standalone mock server (like Mountebank) that runs independently of tests.

**Use Cases:**
- Cross-team contract testing
- CI/CD integration testing
- Language-agnostic service virtualization
- Performance/load testing

**Implementation:**

```bash
# Start mock server from DSL
tdd-dsl serve payment_contract.tdd --port 2525

# Or as part of test runner
tdd-dsl run --target python --with-mocks payment_contract.tdd
```

**Generated Server (Node.js example):**

```javascript
// Generated from DSL
const express = require('express');
const app = express();
app.use(express.json());

const stubs = [
  {
    predicates: [
      { method: 'POST', path: '/api/charge', body: { amount: 100 } }
    ],
    response: { status: 200, body: { id: 'ch_123' } }
  }
];

app.all('*', (req, res) => {
  for (const stub of stubs) {
    if (matches(req, stub.predicates)) {
      return res.status(stub.response.status).json(stub.response.body);
    }
  }
  res.status(404).json({ error: 'No matching stub' });
});

app.listen(4545);
```

### 5.2 Inline Generation

Test doubles embedded directly in generated test code.

**Use Cases:**
- Fast unit tests
- Deterministic test execution
- No external dependencies
- CI-friendly (no port conflicts)

**Comparison:**

| Aspect | Server Mode | Inline Generation |
|--------|-------------|-------------------|
| **Speed** | Slower (network) | Fast (in-process) |
| **Setup** | Requires startup/teardown | Self-contained |
| **Parallelism** | Port management needed | Thread-safe |
| **Debugging** | HTTP inspection tools | Stack traces |
| **CI/CD** | Service orchestration | Simpler |
| **Cross-language** | ✅ Universal | ❌ Per-language |
| **Realism** | High (actual HTTP) | Lower (mocked) |

### 5.3 Hybrid Approach (Recommended)

Support both modes with explicit selection:

```text
mock server "payment_gateway" as gateway:
  mode: inline  # inline | server
  port: 4545   # only for server mode
  protocol: http
  
  stub "successful charge":
    when request: {...}
    then return: {...}
```

**Default Strategy:**
- Unit tests: Inline (fast, deterministic)
- Integration tests: Server (realistic, cross-service)
- CI/CD: Configurable via environment

---

## 6. Contract Validation

### 6.1 Consumer-Driven Contracts

Test doubles as executable contracts between services.

```text
contract "payment-api-v2" as payment_contract:
  consumer: "billing-service"
  provider: "payment-gateway"
  
  request:
    method: "POST"
    path: "/api/v2/charges"
    headers:
      Content-Type: "application/json"
      Authorization: "Bearer {token}"
    body:
      amount: number
      currency: string in ["USD", "EUR", "GBP"]
      
  response:
    status: 201
    body:
      id: string
      status: string in ["pending", "succeeded", "failed"]
      amount: number
      created_at: iso8601
```

### 6.2 Validation Modes

| Mode | Description |
|------|-------------|
| `strict` | Exact match required |
| `loose` | Extra fields allowed |
| `schema` | JSON Schema validation |
| `type` | Type-only matching |

### 6.3 Contract Testing Workflow

```
Consumer Team                    Provider Team
     |                                |
     |  1. Write contract.tdd         |
     |-------------------------------->|
     |                                |
     |  2. Generate mock (inline)     |
     |     Develop against mock       |
     |                                |
     |  3. CI: Verify contract        |
     |-------------------------------->|
     |                                |  4. Implement to satisfy
     |                                |     contract tests
     |                                |
     |  5. Provider CI runs contract  |
     |<--------------------------------|
     |     tests against real API     |
```

### 6.4 Pact-Compatible Output

Optional generation of [Pact](https://pact.io/) contract files:

```json
{
  "consumer": { "name": "billing-service" },
  "provider": { "name": "payment-gateway" },
  "interactions": [
    {
      "description": "successful charge",
      "request": {
        "method": "POST",
        "path": "/api/charge",
        "body": { "amount": 100 }
      },
      "response": {
        "status": 200,
        "body": { "id": "ch_123", "status": "succeeded" }
      }
    }
  ]
}
```

---

## 7. Integration with Existing Emitters

### 7.1 Emitter Architecture Changes

Current emitter interface:

```python
class Emitter(Protocol):
    def emit(self, suite: Suite, target: Target) -> str: ...
```

Extended interface with test doubles:

```python
class EmitterWithMocks(Protocol):
    def emit(self, suite: Suite, target: Target, 
             mocks: List[MockDefinition]) -> str: ...
    
    def emit_mock_setup(self, mock: MockDefinition) -> str: ...
    
    def emit_mock_teardown(self, mock: MockDefinition) -> str: ...
    
    def emit_spy_verification(self, spy: SpyDefinition) -> str: ...
```

### 7.2 AST Extensions

```python
@dataclass
class Suite:
    name: str
    targets: List[Target]
    mocks: List[MockDefinition]  # NEW
    cases: List[Case]

@dataclass  
class MockDefinition:
    name: str
    alias: str
    kind: Literal["server", "function"]
    config: MockConfig
    stubs: List[Stub]

@dataclass
class Stub:
    name: str
    predicate: JsonValue  # Matching criteria
    response: JsonValue   # Return value/response

@dataclass
class SpyDefinition:
    name: str
    alias: str
    verifications: List[SpyVerification]
```

### 7.3 CLI Extensions

```bash
# Generate with mocks
tdd-dsl emit --target python --with-mocks contract.tdd

# Start mock server
tdd-dsl serve contract.tdd --port 2525

# Validate contracts
tdd-dsl validate-contract consumer.tdd provider.tdd

# Generate Pact files
tdd-dsl export --format pact contract.tdd
```

---

## 8. Implementation Roadmap

### Phase 1: Foundation (4-6 weeks)

**Goals:** Parser support, Python/TypeScript inline mocks

| Task | Deliverable |
|------|-------------|
| AST extensions for mocks | `MockDefinition`, `Stub`, `SpyDefinition` dataclasses |
| Parser grammar extension | Support `mock function`, `mock server`, `spy function` |
| Python mock emitter | `unittest.mock` + `responses` integration |
| TypeScript mock emitter | `vitest` + `msw` integration |
| Golden fixtures | Mock/scy test cases |

**Example output:**
```python
# Generated Python with mocks
from unittest.mock import patch, MagicMock

@patch('requests.post')
def test_with_mocked_http(mock_post):
    mock_post.return_value.json.return_value = {"id": "ch_123"}
    # ... test code
```

### Phase 2: HTTP Stub Server (3-4 weeks)

**Goals:** Server mode, multi-language HTTP mocking

| Task | Deliverable |
|------|-------------|
| Standalone mock server | Node.js-based server from DSL |
| `tdd-dsl serve` command | CLI for starting mock servers |
| Java HTTP mocking | `WireMock` integration |
| C# HTTP mocking | `WireMock.Net` integration |
| Configuration format | `mode: inline|server` support |

### Phase 3: Java & C# Support (3-4 weeks)

**Goals:** Enterprise language support with proper mocking

| Task | Deliverable |
|------|-------------|
| Java mock emitter | `Mockito` integration |
| C# mock emitter | `Moq` integration |
| Mock verification patterns | `verify()` call generation |
| Golden fixtures | Java/C# mock test cases |

### Phase 4: Systems Languages (4-6 weeks)

**Goals:** Rust, Go support (systems languages with good mocking ecosystems)

| Task | Deliverable |
|------|-------------|
| Rust mock emitter | `mockall` + `wiremock` integration |
| Go mock emitter | `gomock` + `gock` integration |
| Spy pattern for systems langs | Manual spy implementation |
| Documentation | Emitter-specific guides |

### Phase 5: Odin & Zig (Research Phase)

**Goals:** Determine feasibility and patterns

| Task | Deliverable |
|------|-------------|
| Odin investigation | Interface/dependency injection patterns |
| Zig investigation | Comptime-based mocking feasibility |
| Documentation | "Testing Without Mocks" guide |
| Decision | Full support vs. limited support |

### Phase 6: Contract Testing (4-6 weeks)

**Goals:** Consumer-driven contracts, Pact integration

| Task | Deliverable |
|------|-------------|
| Contract validation | `validate-contract` command |
| Pact export | `--format pact` support |
| Schema validation | JSON Schema generation |
| Documentation | Contract testing guide |

---

## 9. Risk Assessment

### 9.1 Per-Language Risks

| Language | Risk Level | Key Concerns |
|----------|------------|--------------|
| **Python** | 🟢 Low | Mature ecosystem (`unittest.mock`, `responses`) |
| **TypeScript** | 🟢 Low | Excellent tooling (`vitest`, `msw`) |
| **Java** | 🟢 Low | Established patterns (`Mockito`, `WireMock`) |
| **C#** | 🟢 Low | Rich ecosystem (`Moq`, `WireMock.Net`) |
| **Rust** | 🟡 Medium | `mockall` is good but proc macros can be slow; async testing complexity |
| **Go** | 🟡 Medium | `gomock` requires code generation; interface-heavy design needed |
| **Odin** | 🔴 High | No mocking libraries; requires manual DI patterns |
| **Zig** | 🔴 High | Language explicitly avoids mocking; comptime-based testing is different paradigm |

### 9.2 Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Parser complexity** | High | Extend gradually; maintain backward compatibility |
| **Port conflicts** | Medium | Dynamic port allocation; port pools |
| **Async/sync mismatch** | High | Clear documentation; per-language patterns |
| **Performance** | Medium | Inline by default; server opt-in |
| **Maintenance burden** | High | Limit to 4 core languages; document rest |

### 9.3 Design Risks

| Risk | Description | Mitigation |
|------|-------------|------------|
| **Over-complication** | DSL becomes too complex | Keep mocks optional; simple cases remain simple |
| **Leaky abstractions** | Mock details leak into DSL | Per-language config escape hatches |
| **Testing anti-patterns** | Encourage bad mocking practices | Documentation; verification patterns |
| **Version drift** | Mock behavior diverges from real service | Contract validation; periodic sync |

### 9.4 Recommendation: Tiered Support

Given the risks, recommend **tiered support**:

| Tier | Languages | Support Level |
|------|-----------|---------------|
| **Tier 1** | Python, TypeScript, Java, C# | Full feature parity |
| **Tier 2** | Rust, Go | Core mocks; limited server mode |
| **Tier 3** | Odin, Zig | Documentation only; "bring your own" patterns |

---

## 10. Open Questions

### 10.1 Syntax Questions

1. **Should `mock` blocks be global or per-case?**
   - Global: DRY, but less flexibility
   - Per-case: More verbose, but clearer
   - **Proposal:** Global with per-case override capability

2. **How to handle mock lifecycle?**
   - `before_each` / `after_each` patterns
   - Auto-cleanup vs. explicit
   - **Proposal:** Framework-idiomatic lifecycle

3. **Should spies be automatic or declared?**
   - Automatic: Spy on any function
   - Declared: Explicit spy blocks
   - **Proposal:** Declared for clarity

### 10.2 Implementation Questions

1. **Server mode: Node.js or Python?**
   - Node.js: Better async/HTTP ecosystem
   - Python: Consistent with tdd-dsl runtime
   - **Proposal:** Node.js for server; Python for CLI orchestration

2. **How to handle SSL/TLS in server mode?**
   - Self-signed certificates
   - Custom CA
   - **Proposal:** Self-signed with opt-out

3. **Should we support WebSocket mocking?**
   - Adds complexity
   - Real use cases in modern apps
   - **Proposal:** Phase 3 or later

### 10.3 Ecosystem Questions

1. **Pact integration: export only or full compatibility?**
   - Export only: Generate Pact files
   - Full: Run Pact verification
   - **Proposal:** Export first; verify later

2. **OpenAPI integration?**
   - Generate mocks from OpenAPI
   - Generate OpenAPI from mocks
   - **Proposal:** Both directions; future phase

---

## Appendix A: Complete Example Contract

```text
suite "E-commerce Order Flow"
target python "order_service"
target typescript "order-service"
target java "com.example.OrderService"

# Mock external payment gateway
mock server "payment_gateway" as payments:
  mode: inline  # or "server" for standalone
  port: 4545
  protocol: http

  stub "successful charge":
    when request:
      {
        "method": "POST",
        "path": "/api/v1/charges",
        "body": {
          "amount": { "$gt": 0 },
          "currency": { "$in": ["USD", "EUR"] }
        }
      }
    then return:
      {
        "status": 200,
        "body": {
          "id": "ch_{{randomId}}",
          "status": "succeeded",
          "amount": "{{request.body.amount}}"
        }
      }

  stub "declined card":
    when request:
      {"body": {"amount": { "$gte": 10000 }}}
    then return:
      {
        "status": 402,
        "body": {"error": "card_declined", "code": "insufficient_funds"}
      }

# Mock inventory service function
mock function "check_inventory" as inventory:
  when called with:
    [{"sku": "WIDGET-001", "quantity": { "$lte": 100 }}]
  then return:
    {"available": true, "reserved": 10}

  when called with:
    [{"sku": "WIDGET-001", "quantity": { "$gt": 100 }}]
  then return:
    {"available": false, "reason": "insufficient_stock"}

# Spy on notification service
spy function "send_order_confirmation" as notify_spy

case "completes order with payment":
  given mocks:
    [payments, inventory]
  given spies:
    [notify_spy]
  given input:
    {
      "customer_id": "cust_123",
      "items": [{"sku": "WIDGET-001", "qty": 2}],
      "payment": {"card_token": "tok_visa", "amount": 5000}
    }
  when call "create_order"
  then equals:
    {
      "order_id": { "$type": "string" },
      "status": "confirmed",
      "total": 5000
    }
  then spy notify_spy was called:
    {"customer_id": "cust_123", "template": "order_confirmation"}

case "rejects order when payment fails":
  given mocks:
    [payments]
  given input:
    {
      "customer_id": "cust_123",
      "items": [{"sku": "WIDGET-001", "qty": 1000}],
      "payment": {"card_token": "tok_visa", "amount": 99999}
    }
  when call "create_order"
  then equals:
    {"status": "failed", "error": "payment_declined"}
  then spy notify_spy was not called
```

---

## Appendix B: Comparison with Existing Tools

| Tool | Type | TDD DSL Differentiation |
|------|------|------------------------|
| **Mountebank** | HTTP stub server | TDD DSL generates code + runs standalone; multi-language |
| **Pact** | Contract testing | TDD DSL is design-time; Pact is runtime verification |
| **WireMock** | HTTP mocking | TDD DSL generates WireMock configs; broader scope |
| **Mockito** | Java mocking | TDD DSL generates Mockito code; polyglot |
| **MSW** | Browser/Node mocking | TDD DSL generates MSW handlers; declarative DSL |

---

## Summary

Test doubles in TDD DSL represent a **major architectural evolution**:

1. **From tests to complete testing infrastructure** - Not just test code, but mocks and stubs
2. **From single-language to polyglot contracts** - HTTP mocks work across all languages
3. **From verification to contract-driven** - Mocks become executable API specifications

**Key Decisions Needed:**
- Odin/Zig: Full support or documentation-only?
- Server implementation: Node.js or Python?
- Pact integration: Export-only or full compatibility?

**Success Metrics:**
- 4 Tier-1 languages with full mock support
- Server mode for cross-language integration tests
- Contract validation in CI/CD pipelines
- Reduced test setup time vs. manual mocking

---

*Document Version: 1.0*  
*Last Updated: 2026-06-22*  
*Status: Design Complete, Pending Review*
