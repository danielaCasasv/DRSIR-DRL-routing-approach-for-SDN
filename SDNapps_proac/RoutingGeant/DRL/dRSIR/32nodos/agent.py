import numpy as np
import collections
import tensorflow as tf
import time

def dense(x, weights, bias, activation=tf.identity, **activation_kwargs):
    """Dense layer."""
    z = tf.matmul(x, weights) + bias
    # x = x.astype("float32")
    # print("##--x",x)
    # print("##weights",weights)
    return activation(z, **activation_kwargs)


def init_weights(shape, initializer):
    """Initialize weights for tensorflow layer."""
    weights = tf.Variable(
        initializer(shape),
        trainable=True,
        dtype=tf.float32
    )

    return weights


class Network(object):
    """Q-function approximator."""

    def __init__(self,
                 input_size,
                 output_size, lr,
                 # hidden_size=[50, 50],
                 # hidden_size=[32, 32, 32],
                 # hidden_size=[50, 50, 50],
                 hidden_size= [50],#[300],#[50],
                 # hidden_size= [32,64,64,512] ,
                 weights_initializer=tf.initializers.glorot_uniform(),
                 bias_initializer=tf.initializers.zeros(),
                 # optimizer=tf.keras.optimizers.SGD):#,
                 optimizer=tf.optimizers.Adam):#,
                 # **optimizer_kwargs):
        """Initialize weights and hyperparameters."""
        self.input_size = input_size
        self.output_size = output_size
        self.hidden_size = hidden_size

        np.random.seed(41)

        self.initialize_weights(weights_initializer, bias_initializer)
        self.optimizer = optimizer(learning_rate=lr, beta_1=0.9, beta_2=0.999, epsilon=1e-08, amsgrad=False) #Adam tunnable parameters
        # self.optimizer = optimizer(learning_rate=0.0499, momentum=0.0018)#SGD tunnable parameters
        # self.optimizer = optimizer(**optimizer_kwargs) #for default parameters of class
    def initialize_weights(self, weights_initializer, bias_initializer):
        """Initialize and store weights."""
        wshapes = [
            [self.input_size, self.hidden_size[0]],
            # [self.hidden_size[0], self.hidden_size[1]], #3 HL
            # [self.hidden_size[1], self.hidden_size[2]], #3 HL
            # [self.hidden_size[2], self.output_size] #3 HL

            # [self.hidden_size[0], self.hidden_size[1]], #4 HL
            # [self.hidden_size[1], self.hidden_size[2]], #4 HL
            # [self.hidden_size[2], self.hidden_size[3]], #4 HL
            # [self.hidden_size[3], self.output_size] #4 HL

            # [self.hidden_size[0], self.hidden_size[1]], #2 HL
            # [self.hidden_size[1], self.output_size] #2 HL

            [self.hidden_size[0], self.output_size] #1 HL
        ]

        bshapes = [
            [1, self.hidden_size[0]], #1 HL
            # [1, self.hidden_size[1]], #2 HL
            [1, self.output_size] #1 HL

            # [1, self.hidden_size[0]], #3 HL
            # [1, self.hidden_size[1]], #3 HL
            # [1, self.hidden_size[2]], #3 HL
            # [1, self.output_size] #3 HL

            # [1, self.hidden_size[0]], #4 HL
            # [1, self.hidden_size[1]], #4 HL
            # [1, self.hidden_size[2]], #4 HL
            # [1, self.hidden_size[3]], #4 HL
            # [1, self.output_size] #4 HL
        ]

        self.weights = [init_weights(s, weights_initializer) for s in wshapes]
        self.biases = [init_weights(s, bias_initializer) for s in bshapes]

        self.trainable_variables = self.weights + self.biases

    def model(self, inputs):
        """Given a state vector, return the Q values of actions."""
        h1 = dense(inputs, self.weights[0], self.biases[0], tf.nn.relu) #hl 1
        # h2 = dense(h1, self.weights[1], self.biases[1], tf.nn.relu) #hl 2
        # h3 = dense(h2, self.weights[2], self.biases[2], tf.nn.relu) #hl 3
        # out = dense(h3, self.weights[3], self.biases[3]) #2 HL

        out = dense(h1, self.weights[1], self.biases[1]) # 1 HL

        # h2 = dense(h1, self.weights[1], self.biases[1], tf.nn.relu) #HL 4
        # h3 = dense(h2, self.weights[2], self.biases[2], tf.nn.relu) #hl 4
        # h4 = dense(h3, self.weights[3], self.biases[3], tf.nn.relu) #hl 4
        # out = dense(h4, self.weights[4], self.biases[4]) #4 HL

        return out

    def train_step(self, inputs, targets, actions_one_hot):
        """Update weights."""
        with tf.GradientTape() as tape:
            qvalues = tf.squeeze(self.model(inputs))
            preds = tf.reduce_sum(qvalues * actions_one_hot, axis=1) #returns array of q_values per action --> [3,4,5] 3 for action1 , 3 per action 2...
            loss = tf.losses.mean_squared_error(targets, preds)

        grads = tape.gradient(loss, self.trainable_variables)
        self.optimizer.apply_gradients(zip(grads, self.trainable_variables))


class Memory(object):
    """Memory buffer for Experience Replay."""

    def __init__(self, max_size):
        """Initialize a buffer containing max_size experiences."""
        self.buffer = collections.deque(maxlen=max_size)

    def add(self, experience):
        """Add an experience to the buffer."""
        self.buffer.append(experience)

    def sample(self, batch_size):
        """Sample a batch of experiences from the buffer."""
        buffer_size = len(self.buffer)
        index = np.random.choice(
            np.arange(buffer_size),
            size=batch_size,
            replace=False
        )

        return [self.buffer[i] for i in index]

    def __len__(self):
        """Interface to access buffer length."""
        return len(self.buffer)


class Agent(object):
    """Deep Q-learning agent."""

    def __init__(self,
                 state_space_size,
                 action_space_size,
                 target_update_freq=900, #1000, #cada n steps se actualiza la target network
                 discount=0.7,
                 batch_size=15,
                 max_explore=1,
                 min_explore=0.05,
                 anneal_rate=(1/1500), #1/100000),
                 replay_memory_size = 100000,#100000,
                 replay_start_size= 200, #300 #despues de n steps comienza el replay
                 lr = 0.001):
        """Set parameters, initialize network.""" 
        #parameter optimizer
        self.lr = lr
        
        self.action_space_size = action_space_size

        self.online_network = Network(state_space_size, action_space_size, lr)
        self.target_network = Network(state_space_size, action_space_size, lr)

        self.update_target_network()

        # training parameters
        self.target_update_freq = target_update_freq
        self.discount = discount
        self.batch_size = batch_size

        # policy during learning
        self.max_explore = max_explore + (anneal_rate * replay_start_size)
        self.min_explore = min_explore
        self.anneal_rate = anneal_rate
        self.steps = 0

        # replay memory
        self.replay_memory_size = replay_memory_size
        self.memory = Memory(replay_memory_size)
        self.replay_start_size = replay_start_size
        self.experience_replay = Memory(replay_memory_size)



    def handle_episode_start(self):
        self.last_state, self.last_action = None, None

    def step(self, state, reward, training=True):
        """Observe state and rewards, select action.
        It is assumed that `observation` will be an object with
        a `state` vector and a `reward` float or integer. The reward
        corresponds to the action taken in the previous step.
        """
        i = time.time()
        last_state, last_action = self.last_state, self.last_action
        last_reward = reward
        # state = state
        
        action = self.policy(state, training)

        if training:
            self.steps += 1

            if last_state:
                experience = {
                    "state": last_state,
                    "action": last_action,
                    "reward": last_reward,
                    "next_state": state
                }

                self.memory.add(experience)

            if self.steps > self.replay_start_size:
                self.train_network()

                if self.steps % self.target_update_freq == 0:
                    self.update_target_network()
# 
                    # print('     Step time updtade ', time.time()-i, self.steps)


        self.last_state = state
        self.last_action = action

        # print('         Agent step time:', time.time()-i)
        return action

    def policy(self,state, training):
        """Epsilon-greedy policy for training, greedy policy otherwise."""
        # print(state, training)

        explore_prob = self.max_explore - (self.steps * self.anneal_rate)
        explore = max(explore_prob, self.min_explore) > np.random.rand() #r < pr Exploit, else Explore
        # print(self.max_explore, explore_prob)

        if training and explore:
            action = np.random.randint(self.action_space_size)
        else:
            inputs = np.expand_dims(state, 0) #expands dimension in axis 0 ... If state was shape (2,3) --> (1,2,3)
            qvalues = self.online_network.model(inputs)
            action = np.squeeze(np.argmin(qvalues, axis=-1)) #reward reflects in min values as it defines the cost of the path
            # if int(action) != 0:
            #     print(int(action)) #para ver que onda 
            #returns the index of the action taken

        return action

    def update_target_network(self):
        """Update target network weights with current online network values."""
        variables = self.online_network.trainable_variables
        variables_copy = [tf.Variable(v) for v in variables]
        self.target_network.trainable_variables = variables_copy

    def train_network(self):
        """Update online network weights."""
        batch = self.memory.sample(self.batch_size)
        inputs = np.array([b["state"] for b in batch])
        actions = np.array([b["action"] for b in batch])
        rewards = np.array([b["reward"] for b in batch])
        next_inputs = np.array([b["next_state"] for b in batch])
        # print('train', next_inputs, type(next_inputs),len(next_inputs),len(next_inputs[0]))
        # print('train', actions, type(actions),len(actions))

        actions_one_hot = np.eye(self.action_space_size)[actions]
        # print(actions_one_hot)

        next_qvalues = np.squeeze(self.target_network.model(next_inputs))
        targets = rewards + self.discount * np.amin(next_qvalues, axis=-1) #My reward is cost path. I need to minimize it

        self.online_network.train_step(inputs, targets, actions_one_hot)


# def train_(episode):

#     loss = []
#     agent = Agent()
#     for e in range(episode):
#         state = env.reset()
#         state = np.reshape(state, (1, 5))
#         score = 0
#         max_steps = 1000
#         for i in range(max_steps):
#             action = agent.act(state)
#             reward, next_state, done = env.step(action)
#             score += reward
#             next_state = np.reshape(next_state, (1, 5))
#             agent.remember(state, action, reward, next_state, done)
#             state = next_state
#             agent.replay()
#             if done:
#                 print("episode: {}/{}, score: {}".format(e, episode, score))
#                 break
#         loss.append(score)
#     return loss




#Recuperar valores max de una lista
# x = np.array([4,2,3])
# index_array = np.argmax(x, axis=-1) #Encuentra el indice del valor max del array
# np.take_along_axis(x,np.expand_dims(index_array, axis=-1), axis=-1) #recupera el valor del aquel indice
