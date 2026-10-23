// PaperForge marking-scheme template.
//
// Renders the marking scheme that belongs to a PaperForge paper specification
// (JSON): the same file that drives templates/paper.typ, so the paper and its
// scheme can never drift apart. Usage from a driver file:
//
//   #import "templates/scheme.typ": render-scheme
//   #render-scheme(json("spec.json"))
//
// Wherever a question offers an internal choice, the scheme prints the main
// answer's value points followed by the alternative's, mirroring the choice
// exactly as the auditor (audit.py) requires.

#let _scheme-entry(q) = {
  let scheme = q.at("scheme", default: none)
  block(below: 0.7em, breakable: true)[
    #text(weight: "bold")[#q.id.] #h(1fr) (#q.marks mark#if q.marks != 1 [s])
    #if scheme == none {
      linebreak()
      text(style: "italic")[No scheme entry.]
    } else {
      if scheme.at("answer", default: none) != none {
        linebreak()
        "Answer: " + scheme.answer
      }
      if scheme.at("value_points", default: none) != none {
        for point in scheme.value_points {
          linebreak()
          h(1.2em)
          "- " + point
        }
      }
      if scheme.at("marks_split", default: none) != none {
        linebreak()
        text(style: "italic")[Mark split: #scheme.marks_split]
      }
      if scheme.at("alternative_value_points", default: none) != none {
        linebreak()
        text(weight: "bold")[OR (alternative):]
        for point in scheme.alternative_value_points {
          linebreak()
          h(1.2em)
          "- " + point
        }
        if scheme.at("alternative_marks_split", default: none) != none {
          linebreak()
          text(style: "italic")[Mark split: #scheme.alternative_marks_split]
        }
      }
    }
  ]
}

#let render-scheme(spec) = {
  set page(paper: "a4", margin: (x: 20mm, top: 18mm, bottom: 18mm))
  set text(size: 11pt)
  set par(justify: true, leading: 0.75em)

  let p = spec.paper

  align(center)[
    #text(size: 15pt, weight: "bold")[Marking Scheme]
    #linebreak()
    #text(size: 13pt, weight: "bold")[#p.subject]
    #linebreak()
    Class: #p.class #h(1em) Maximum Marks: #p.max_marks
  ]
  v(0.4em)
  line(length: 100%)
  v(0.4em)
  text(style: "italic")[
    General note: accept any answer that conveys the value points below,
    in the candidate's own words, unless the question demands a specific
    form. Award marks for the steps shown, not only for the final answer.
  ]
  v(0.6em)

  for section in spec.sections {
    heading(level: 2)[Section #section.id -- #section.title]
    for q in section.questions {
      _scheme-entry(q)
    }
  }
}
