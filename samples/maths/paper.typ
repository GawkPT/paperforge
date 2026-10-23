// Sample driver: renders the Mathematics sample paper.
// Compile from the repository root:
//   typst compile --root . samples/maths/paper.typ
#import "../../templates/paper.typ": render-paper
#render-paper(json("spec.json"))
