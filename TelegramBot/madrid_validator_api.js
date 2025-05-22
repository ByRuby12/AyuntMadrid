// # # Esta función se encarga de validar la ubicación del usuario usando una API externa (Node.js).
// # # Si la ubicación es válida, devuelve True; de lo contrario, devuelve False.
// def validar_ubicacion_node(lat, lon):
//     try:
//         response = requests.post(
//             "http://localhost:3001/validate",
//             json={"lat": lat, "lon": lon},
//             timeout=2
//         )
//         if response.status_code == 200:
//             return response.json().get("inside", False)
//         return False
//     except Exception as e:
//         print(f"Error llamando a la API Node.js: {e}")
//         return False

const express = require('express');
const cors = require('cors');
const app = express();
const port = 3001;

const madridPolygon = [
  [40.3356, -3.8880],  // Suroeste (Villaverde/Carabanchel)
  [40.3356, -3.5179],  // Sureste (Vicálvaro/Vallecas)
  [40.6453, -3.5179],  // Noreste (Fuencarral/Barajas)
  [40.6453, -3.8880],  // Noroeste (El Pardo/Moncloa)
  [40.3356, -3.8880]   // Cierra el polígono
];

function isInsideMadrid(lat, lon) {
  let x = lon, y = lat;
  let inside = false;
  for (let i = 0, j = madridPolygon.length - 1; i < madridPolygon.length; j = i++) {
    let xi = madridPolygon[i][1], yi = madridPolygon[i][0];
    let xj = madridPolygon[j][1], yj = madridPolygon[j][0];
    let intersect = ((yi > y) !== (yj > y)) &&
      (x < (xj - xi) * (y - yi) / ((yj - yi) || 1e-10) + xi);
    if (intersect) inside = !inside;
  }
  return inside;
}

app.use(cors());
app.use(express.json());

app.post('/validate', (req, res) => {
  const { lat, lon } = req.body;
  if (typeof lat !== 'number' || typeof lon !== 'number') {
    return res.status(400).json({ error: 'lat and lon must be numbers' });
  }
  const inside = isInsideMadrid(lat, lon);
  res.json({ inside });
});

app.listen(port, () => {
  console.log(`Madrid validator API listening at http://localhost:${port}`);
});
