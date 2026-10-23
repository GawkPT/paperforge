// Sample driver: renders the English sample paper.
// Compile from the repository root:
//   typst compile --root . samples/english/paper.typ
#import "../../templates/paper.typ": render-paper
#render-paper(json("spec.json"))
