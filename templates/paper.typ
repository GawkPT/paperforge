// PaperForge question-paper template.
//
// Renders a complete, print-ready question paper from a PaperForge paper
// specification (JSON). Usage from a driver file:
//
//   #import "templates/paper.typ": render-paper
//   #render-paper(json("spec.json"))
//
// The template is deliberately plain: a generic school-examination face with
// no institution name or branding. Branding belongs in a local wrapper, not
// in the paper itself.

#let _marks(n) = {
  if n == 1 { "(1 mark)" } else { "(" + str(n) + " marks)" }
}

#let _question(q) = {
  block(below: 0.7em, breakable: true)[
    #if q.at("passage", default: none) != none {
      block(
        inset: 8pt,
        stroke: 0.5pt + gray,
        below: 0.6em,
        width: 100%,
      )[#q.passage]
    }
    #text(weight: "bold")[#q.id.] #q.prompt #h(1fr) #_marks(q.marks)
    #if q.at("options", default: none) != none {
      for (i, opt) in q.options.enumerate() {
        linebreak()
        h(1.2em)
        "(" + ("a", "b", "c", "d", "e", "f").at(i) + ") " + opt
      }
    }
    #if q.at("word_limit", default: none) != none {
      linebreak()
      text(style: "italic")[Word limit: about #q.word_limit words.]
    }
    #if q.at("choice", default: none) != none {
      linebreak()
      align(center)[#text(weight: "bold")[OR]]
      q.choice.alternative_prompt
      h(1fr)
      _marks(q.marks)
      if q.choice.at("alternative_word_limit", default: none) != none {
        linebreak()
        text(style: "italic")[Word limit: about #q.choice.alternative_word_limit words.]
      }
    }
  ]
}

#let render-paper(spec) = {
  set page(paper: "a4", margin: (x: 20mm, top: 18mm, bottom: 18mm))
  set text(size: 11pt)
  set par(justify: true, leading: 0.75em)

  let p = spec.paper

  align(center)[
    #text(size: 15pt, weight: "bold")[#p.title]
    #linebreak()
    #text(size: 13pt, weight: "bold")[#p.subject]
    #linebreak()
    Class: #p.class
  ]
  v(0.4em)
  grid(
    columns: (1fr, 1fr),
    [Time allowed: #p.time_allowed],
    align(right)[Maximum Marks: #p.max_marks],
  )
  line(length: 100%)
  v(0.2em)
  [Name: ..............................................]
  h(1em)
  [Roll No.: ..............................]
  v(0.6em)

  text(weight: "bold")[General Instructions:]
  for (i, instruction) in p.general_instructions.enumerate() {
    linebreak()
    str(i + 1) + ". " + instruction
  }
  v(0.4em)
  line(length: 100%)

  for section in spec.sections {
    let subtotal = section.questions.map(item => item.marks).sum()
    heading(level: 2)[
      Section #section.id -- #section.title #h(1fr) (#subtotal marks)
    ]
    if section.at("instructions", default: none) != none {
      text(style: "italic")[#section.instructions]
      v(0.3em)
    }
    if section.at("materials", default: none) != none {
      for material in section.materials {
        block(
          inset: 8pt,
          stroke: 0.5pt + gray,
          below: 0.6em,
          width: 100%,
        )[
          #text(weight: "bold")[#material.label]
          #linebreak()
          #material.text
        ]
      }
    }
    for q in section.questions {
      _question(q)
    }
  }
}
