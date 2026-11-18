# Keyboard BOM 与图谱语义规范

## 1. Configurations are alternatives, not additive shopping lists
```
external_keyboard
├── switch_technology: one_of [MX_contact, Hall_magnetic, membrane_dome, optical_optional]
├── connection: one_of [USB_wired, BLE, proprietary_2_4GHz]
├── keycap: one_of [PBT_mix, ABS, optional_PC]
├── power: wired=USB_bus_power; wireless=one_of [Li_ion, primary_cells]
├── mounting: one_of [steel_plate, aluminium_plate, FR4_plate, plate_less]
└── optional: [RGB, hot_swap, gasket, knob, split]
```
A tree node of kind `category` or `configuration` must use `associated_with` as a navigation/class edge, not an actual material-input proof. The technology path `material_input` must be supported by independent components and scope. When the choice is unknown, record several alternatives as separate candidate hypotheses without merging them into one BOM.

## 2. Node taxonomy
- Product `keyboard` root; `configuration` choice, `component` physical component, `material` raw or compounded material, `chemical` industrial intermediate, `process` production/firmware, `equipment` enabling machinery, `resource` natural resource, `standard` public protocol, `software` code, `company_role` industry participant, `channel` distribution.
- `component_of` means a part of a scoped product assembly; do not use on product-brand association.
- `associated_with` is topic association and may carry only technological/hypothesis status, never interpreted as current customer purchase.
- `uses_equipment` must distinguish factory production machinery from parts consumed in the delivered keyboard.
- Cross-link direction is upstream→downstream; do not duplicate an identical parent edge. Existing `edge` uniqueness enforces three-tuple + product context.

## 3. Example deep technical chains
Keycap → PBT compounded grade → PBT polymer → PTA + BDO → aromatic petrochemicals / chemical synthesis → crude oil or alternate feedstock. Beware PBTfans warns its PBT keycaps need not be pure PBT.
Mechanical switch → spring/contact/stem/housing → metal spring wire, gold plating, precision molding → smelting / petrochemicals → resources.
Hall switch → magnet + Hall IC → magnet raw materials + silicon wafer / lithography → mining / refining; do not imply all Hall sensors use neodymium magnets.
PCB → copper clad FR-4 → copper foil + woven fiberglass + thermoset epoxy → metals and chemical precursors.
Wireless keyboard → BLE SoC + rechargeable or disposable battery → wireless semiconductors and power chain. HID standard/firmware is a nonmaterial dependency.

## 4. Product data: public snapshot schema
`data/products/keyboard/product.json` is classified under `electronics`. `graph.json` uses `atlas_v1.1`: `nodes`, `materials`, `companies`, `company_material`, `sources`, `cross_links`, `node_intelligence`, `product_configurations`; company purchase edges stay empty unless a primary record proves them. All nodes receive `research_coverage.py` stages and tasks after build.
