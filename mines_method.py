    def skibidimines(self):
        if not self.check_game():
            return "*Currently not in game. Please start a game and run command again.*\n", "N/A", "N/A", "None"

        r2 = scraper.get("https://api.bloxflip.com/games/mines", headers=self.headers)
        data_game = json.loads(r2.text)
        mines_amount = data_game['game']['minesAmount']
        uuid = data_game['game']['uuid']
        bet_amount = data_game['game']['betAmount']
        nonce = data_game['game']['nonce'] - 1
        hash_id = data_game['game']['_id']['$oid']
        random_accuracy = random.uniform(85, 95)

        r = scraper.get('https://api.bloxflip.com/games/mines/history',
                        headers=self.headers,
                        params={"size": '5', "page": '0'})
        data = r.json()['data'][0]
        mines_location = data['mineLocations']
        clicked_spots = data['uncoveredLocations']

        def calculate_bomb_likelihood_mrf(spot, clicked_spots, mines_location, grid_size):
            bomb_likelihood = 0.0
            row, col = spot // grid_size, spot % grid_size
    
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    nr, nc = row + dr, col + dc
                    neighbor_spot = nr * grid_size + nc
            
            if 0 <= nr < grid_size and 0 <= nc < grid_size and neighbor_spot not in clicked_spots:
                if neighbor_spot in mines_location:
                    bomb_likelihood += 0.3
                bomb_likelihood += 0.1
    
            return min(bomb_likelihood, 0.9)

        def mrf_objective(x, *args):
            grid_size, clicked_spots, mines_location = args
            likelihood = 0.0
    
            for spot in range(grid_size ** 2):
                if spot not in clicked_spots and spot not in mines_location:
                    likelihood -= x[spot] * calculate_bomb_likelihood_mrf(spot, clicked_spots, mines_location, grid_size)
    
            return likelihood

        def predict_safe_tiles_mrf(clicked_spots, mines_location, grid_size, num_safe_tiles):
            x0 = np.random.rand(grid_size ** 2)
            bounds = [(0, 1)] * (grid_size ** 2)
    
            result = minimize(mrf_objective, x0, args=(grid_size, clicked_spots, mines_location), bounds=bounds, method='L-BFGS-B')
    
            probabilities = result.x
    
            safe_spots_indices = np.argsort(probabilities)[:num_safe_tiles]
    
            grid_display = [['❌'] * grid_size for _ in range(grid_size)]
    
            for spot in clicked_spots:
                row, col = divmod(spot, grid_size)
                grid_display[row][col] = '❌'
    
            for spot in safe_spots_indices:
                row, col = divmod(spot, grid_size)
                grid_display[row][col] = '✅'
    
            grid_display_str = '\n'.join(''.join(row) for row in grid_display)
    
            return grid_display_str

        grid_size = 5
        num_safe_tiles = self.max_tiles

        predicted_grid = predict_safe_tiles_mrf(clicked_spots, mines_location, grid_size, num_safe_tiles)

        return predicted_grid, mines_amount, bet_amount, uuid
