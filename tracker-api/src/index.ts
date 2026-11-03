import app from './app'

const PORT = Number(process.env.PORT) || 3000

console.log(
  `[startup] USE_FACEBOOK_AUTH=${JSON.stringify(process.env.USE_FACEBOOK_AUTH)}`,
)

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server listening on port ${PORT}`)
})
