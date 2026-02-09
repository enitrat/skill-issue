# D2 Syntax Reference

## Core Syntax Elements

### Basic Shapes and Connections

```d2
# Simple connection
A -> B

# Labeled connection
A -> B: Connection Label

# Multiple connections
A -> B
A -> C
B -> C
```

### Shape Properties

```d2
# Default shape (rectangle)
myShape

# Shape with label
myShape: My Shape Label

# Shape with custom type
server: Web Server {
  shape: rectangle
}

database: Database {
  shape: cylinder
}

user: End User {
  shape: person
}
```

### Available Shape Types

- `rectangle` - Default, basic rectangular shape
- `square` - Square shape
- `circle` - Circular shape
- `oval` - Oval shape
- `diamond` - Diamond shape
- `hexagon` - Hexagonal shape
- `parallelogram` - Parallelogram shape
- `cylinder` - Cylindrical shape (good for databases)
- `queue` - Queue shape
- `package` - Package shape
- `step` - Step shape
- `callout` - Callout shape
- `stored_data` - Stored data shape
- `person` - Person icon shape
- `document` - Document shape
- `page` - Page shape
- `cloud` - Cloud shape
- `text` - Text-only (no border)
- `code` - Code block
- `class` - Class diagram element
- `sql_table` - SQL table element
- `sequence_diagram` - Sequence diagram
- `image` - Image shape (use with icon property)

## Containers (Grouping)

### Nested Containers

```d2
# Using dot notation
parent.child1
parent.child2
parent.child1 -> parent.child2

# Using nested syntax
parent: {
  child1
  child2
  child1 -> child2
}

# Container with label
cloud_services: Cloud Services {
  aws: AWS {
    ec2: EC2
    s3: S3
  }
  gcp: GCP {
    compute: Compute Engine
    storage: Cloud Storage
  }
}
```

### Cross-Container Connections

```d2
frontend.ui -> backend.api
backend.api -> database.postgres
```

### Parent Reference (_)

```d2
container: {
  child1
  child2
  
  # Reference parent from within
  _.external -> child1
}

external
```

## Styling

### Individual Styles

```d2
# Style properties
element: {
  style.fill: "#4A90E2"
  style.stroke: "#2E5C8A"
  style.stroke-width: 2
  style.stroke-dash: 5
  style.shadow: true
  style.opacity: 0.8
  style.font-size: 16
  style.bold: true
  style.italic: true
  style.underline: true
  style.3d: true
  style.multiple: true
  style.animated: true
}

# Connection styles
A -> B: {
  style.stroke: "#FF5733"
  style.stroke-width: 3
  style.stroke-dash: 3
  style.animated: true
}
```

### Classes (Reusable Styles)

```d2
classes: {
  primary: {
    style.fill: "#4A90E2"
    style.stroke: "#2E5C8A"
    style.stroke-width: 2
  }
  
  secondary: {
    style.fill: "#E2E8F0"
    style.stroke: "#94A3B8"
  }
  
  database_style: {
    shape: cylinder
    style.fill: "#48C774"
    style.multiple: true
  }
}

# Apply classes
element1: {
  class: primary
}

element2: {
  class: secondary
}

db: {
  class: database_style
}
```

## Icons

### Using Icons

```d2
# Icon with shape
server: {
  icon: https://icons.terrastruct.com/tech/docker.svg
  shape: image
}

# Icon with label
app: Application {
  icon: https://icons.terrastruct.com/aws/Compute/AWS-Lambda.svg
}

# Note: Icons must be accessible via HTTP/HTTPS
# Use shape: image to display icon without border
```

## Connection Types

### Arrow Types

```d2
# Standard arrow (->)
A -> B

# Bidirectional (<->)
A <-> B

# No arrowhead (--) 
A -- B

# Reversed arrow (<-)
A <- B
```

### Arrowhead Customization

```d2
A -> B: {
  source-arrowhead: {
    shape: diamond
    style.filled: true
  }
  target-arrowhead: {
    shape: arrow
    label: Target
  }
}

# Available arrowhead shapes:
# arrow, triangle, diamond, circle, cf-one, cf-one-required, cf-many, cf-many-required
```

## Layout and Positioning

### Direction

```d2
direction: right  # Options: up, down, left, right

# Direction for specific containers
container: {
  direction: down
  A -> B -> C
}
```

### Grid Layouts

```d2
container: {
  grid-rows: 3
  grid-columns: 2
  grid-gap: 20
  
  item1
  item2
  item3
  item4
  item5
  item6
}
```

### Width and Height

```d2
element: {
  width: 200
  height: 100
}
```

## Special Objects

### SQL Tables

```d2
users: {
  shape: sql_table
  id: int {constraint: primary_key}
  name: varchar
  email: varchar
  created_at: timestamp
}
```

### Classes (UML)

```d2
MyClass: {
  shape: class
  
  -privateField: string
  +publicField: int
  #protectedField: bool
  
  +publicMethod()
  -privateMethod()
  #protectedMethod()
}
```

### Code Blocks

```d2
example: |`go
  func main() {
    fmt.Println("Hello, World!")
  }
`|
```

### Markdown

```d2
explanation: |md
  # Title
  
  This is **markdown** text with:
  - Lists
  - Links
  - Formatting
|
```

## Advanced Features

### Notes

```d2
element: {
  near: top-center
}

element.note: This is a note explaining the element {
  shape: text
}
```

### Links and Tooltips

```d2
element: {
  link: https://example.com
  tooltip: Click to visit our website
}
```

### Scenarios/Layers

```d2
# Base layer
A -> B

# Scenario 1
scenarios: {
  error_case: {
    A.style.fill: red
    B.style.fill: red
    A -> B: Error {
      style.stroke: red
    }
  }
}
```

## Variables and Configuration

### Using Variables

```d2
vars: {
  primary-color: "#4A90E2"
  secondary-color: "#E2E8F0"
}

element: {
  style.fill: ${primary-color}
}
```

### D2 Configuration

```d2
vars: {
  d2-config: {
    layout-engine: elk  # Options: dagre (default), elk
    theme-id: 0         # Theme number
    sketch: true        # Hand-drawn style
    pad: 100            # Padding around diagram
  }
}
```

## Best Practices

1. **Use meaningful IDs**: Choose descriptive IDs for shapes that reflect their purpose
2. **Group related elements**: Use containers to organize related components
3. **Apply consistent styling**: Use classes for consistent visual appearance
4. **Label connections clearly**: Add descriptive labels to connections
5. **Leverage direction**: Use direction to improve diagram flow
6. **Use appropriate shapes**: Match shape types to what they represent (cylinder for databases, person for users, etc.)
7. **Add icons sparingly**: Icons enhance understanding but can clutter if overused
8. **Keep it simple**: Start with core elements and add complexity as needed
9. **Use notes for context**: Add explanatory notes where additional context helps
10. **Test layouts**: Try different layout engines (dagre vs elk) for optimal results

## Common Patterns

### Microservices Architecture

```d2
direction: right

users: Users {
  shape: person
}

api_gateway: API Gateway {
  shape: hexagon
}

services: Services {
  auth: Auth Service {
    shape: rectangle
  }
  users: User Service {
    shape: rectangle
  }
  orders: Order Service {
    shape: rectangle
  }
}

database: Databases {
  auth_db: Auth DB {
    shape: cylinder
  }
  users_db: Users DB {
    shape: cylinder
  }
  orders_db: Orders DB {
    shape: cylinder
  }
}

users -> api_gateway
api_gateway -> services.auth
api_gateway -> services.users
api_gateway -> services.orders
services.auth -> database.auth_db
services.users -> database.users_db
services.orders -> database.orders_db
```

### Data Flow

```d2
direction: right

source: Data Source {
  shape: cylinder
  style.multiple: true
}

etl: ETL Process {
  shape: hexagon
}

warehouse: Data Warehouse {
  shape: stored_data
}

analytics: Analytics {
  shape: rectangle
}

visualization: Dashboard {
  shape: page
}

source -> etl: Extract
etl -> warehouse: Load
warehouse -> analytics: Query
analytics -> visualization: Display
```

### Network Topology

```d2
direction: down

internet: Internet {
  shape: cloud
}

firewall: Firewall {
  shape: hexagon
}

dmz: DMZ {
  web_server: Web Server {
    shape: rectangle
  }
}

internal: Internal Network {
  app_server: App Server {
    shape: rectangle
  }
  db_server: Database {
    shape: cylinder
  }
}

internet -> firewall
firewall -> dmz.web_server
dmz.web_server -> internal.app_server
internal.app_server -> internal.db_server
```
