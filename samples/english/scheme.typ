// Sample driver: renders the English sample marking scheme.
// Compile from the repository root:
//   typst compile --root . samples/english/scheme.typ
#import "../../templates/scheme.typ": render-scheme
#render-scheme(json("spec.json"))
