// Sample driver: renders the Mathematics sample marking scheme.
// Compile from the repository root:
//   typst compile --root . samples/maths/scheme.typ
#import "../../templates/scheme.typ": render-scheme
#render-scheme(json("spec.json"))
