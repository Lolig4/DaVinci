**Ha Card:**
```
type: custom:flex-table-card
entities:
  - entity: sensor.davinci_timetable
columns:
  - data: "1"
    name: Mo
    modify: |-
      if (x.current) {
        '<span style="color: green;">' + x.subject + '\n' + x.teacher + '\n' + x.room + '</span>'
      } else {[x.subject, x.teacher, x.room].join('\n')}
  - data: "2"
    name: Di
    modify: |-
      if (x.current) {
        '<span style="color: green;">' + x.subject + '\n' + x.teacher + '\n' + x.room + '</span>'
      } else {[x.subject, x.teacher, x.room].join('\n')}
  - data: "3"
    name: Mi
    modify: |-
      if (x.current) {
        '<span style="color: green;">' + x.subject + '\n' + x.teacher + '\n' + x.room + '</span>'
      } else {[x.subject, x.teacher, x.room].join('\n')}
  - data: "4"
    name: Do
    modify: |-
      if (x.current) {
        '<span style="color: green;">' + x.subject + '\n' + x.teacher + '\n' + x.room + '</span>'
      } else {[x.subject, x.teacher, x.room].join('\n')}
  - data: "5"
    name: Fr
    modify: |-
      if (x.current) {
        '<span style="color: green;">' + x.subject + '\n' + x.teacher + '\n' + x.room + '</span>'
      } else {[x.subject, x.teacher, x.room].join('\n')}
css:
  td: |
    white-space: pre;
```

**Prerequisites:**
- HACS with [flex-table-card](https://github.com/custom-cards/flex-table-card) installed