import cv2
import numpy as np
from skimage.metrics import structural_similarity


class EventCameraEmulator(object):

    def get_events_image(self, image_1, image_2, theta=20, record_off_events=True):
        '''
        Returns an emulated event image from two RGB images.
        This may be extended to be usable with different event emulation strategies.

        Parameters
        ----------
        image_1: numpy.ndarray
            Current RGB image array.
        image_2: numpy.ndarray
            Previous RGB image array.
        theta: int
            Threshold value. Smaller values lead to more noisy results.
        
        Returns
        -------
        events_image: numpy.ndarray
            Estimated event image array.
        '''
        image_1_gray = cv2.cvtColor(image_1, cv2.COLOR_BGR2GRAY)
        image_2_gray = cv2.cvtColor(image_2, cv2.COLOR_BGR2GRAY)

        events_image = self.compute_thresholded_diff_events_image(image_1_gray, image_2_gray, theta, record_off_events)

        return events_image

    def compute_thresholded_diff_events_image(self, frame, previous_frame, theta=20, record_off_events=True):
        '''
        Performs a custom procedure to compute a thresholded difference between two frames:
         - subtracting two GRAY frames from each other,
         - identifying ON and OFF events as pixels with values greater than theta and values
           less than -theta, respectively
         - emulating an event image by marking ON and OFF events with red and blue in a white frame

        Parameters
        ----------
        frame: numpy.ndarray
            Current GRAY image array.
        previous_frame: numpy.ndarray
            Previous GRAY image array.
        theta: int
            Threshold value. Smaller values lead to more noisy results.
        
        Returns
        -------
        event_frame: numpy.ndarray
            Estimated event image array.
        '''
        ## Frames must be cast to signed ints before computing diffs
        ## Otherwise, negative numbers wrap around to 255...
        diff_frame = frame.astype(int) - previous_frame.astype(int)

        event_frame = np.full((frame.shape[0], frame.shape[1], 3), 255., dtype='uint8')
        event_frame[diff_frame > theta] = [255., 0., 0.]
        if record_off_events:
            event_frame[diff_frame < -theta] = [0., 0., 255.]

        return event_frame

    def get_ssim_diff_frame(self, image_1, image_2, rounding_threshold=50):
        '''
        Computes the difference between two frames using scikit-image's structural
        similarity index approach.

        Parameters
        ----------
        image_1: numpy.ndarray
            Current RGB image array.
        image_2: numpy.ndarray
            Previous RGB image array.
        rounding_threshold: int
            Pixel filtering threshold. Helps in some noise filtering by setting values that are
            close to white or black to these colors
        
        Returns
        -------
        diff_frame: numpy.ndarray
            Estimated event image array.
        '''
        score, diff_frame = structural_similarity(image_1, image_2, full=True)
        diff_frame = (diff_frame * 255).astype("uint8")

        diff_frame[diff_frame > (255 - rounding_threshold)] = 255
        diff_frame[diff_frame < (0 + rounding_threshold)] = 0
        
        return diff_frame

    def get_events_image_rgb(self, image_1, image_2, theta=20, record_off_events=True):
        '''
        Returns an emulated event image from two RGB images.
        This may be extended to be usable with different event emulation strategies.

        Parameters
        ----------
        image_1: numpy.ndarray
            Current RGB image array.
        image_2: numpy.ndarray
            Previous RGB image array.
        theta: int
            Threshold value. Smaller values lead to more noisy results.
        
        Returns
        -------
        events_image: numpy.ndarray
            Estimated event image array.
        '''
        image_1_rgb = cv2.cvtColor(image_1, cv2.COLOR_BGR2RGB)
        image_2_rgb = cv2.cvtColor(image_2, cv2.COLOR_BGR2RGB)

        events_image = self.compute_thresholded_diff_events_image_rgb_ALL(image_1_rgb, image_2_rgb, theta, record_off_events)
        # events_image = self.compute_thresholded_diff_events_image_rgb_ONE(image_1_rgb, image_2_rgb, theta, record_off_events)

        return events_image

    def compute_thresholded_diff_events_image_rgb_ALL(self, frame, previous_frame, theta=20, record_off_events=True):
        '''
        Performs a custom procedure to compute a thresholded difference between two frames:
         - subtracting two RGB frames from each other,
         - identifying ON and OFF events as pixels with values greater than theta and values
           less than -theta, respectively
         - emulating an event image by marking ON and OFF events with red and blue in a white frame

        Parameters
        ----------
        frame: numpy.ndarray
            Current RGB image array.
        previous_frame: numpy.ndarray
            Previous RGB image array.
        theta: int
            Threshold value. Smaller values lead to more noisy results.
        
        Returns
        -------
        event_frame: numpy.ndarray
            Estimated event image array.
        '''
        ## Frames must be cast to signed ints before computing diffs
        ## Otherwise, negative numbers wrap around to 255...
        diff_frame = frame.astype(int) - previous_frame.astype(int)
        theta_frame = np.full((diff_frame.shape[0], diff_frame.shape[1], 3), theta, dtype='uint8')

        ## Find indices of pixels for which R,G,B are all > theta:
        bools = (diff_frame - theta_frame) > 0.
        # Note: If RGB are all True, the sum for a pixel would be 3:
        on_indices = np.sum(bools, 2) == 3.

        ## Find indices of pixels for which R,G,B are all < theta:
        bools = (diff_frame + theta_frame) < 0.
        # Note: If RGB are all True, the sum for a pixel would be 3:
        off_indices = np.sum(bools, 2) == 3.

        event_frame = np.full((frame.shape[0], frame.shape[1], 3), 255., dtype='uint8')

        event_frame[on_indices] = [255., 0., 0.]
        if record_off_events:
            event_frame[off_indices] = [0., 0., 255.]
            # event_frame[off_indices] = [255., 0., 0.]    ## temp change to consider both ON and OFF events

        return event_frame

    def compute_thresholded_diff_events_image_rgb_ONE(self, frame, previous_frame, theta=20, record_off_events=True):
        '''
        Performs a custom procedure to compute a thresholded difference between two frames:
         - subtracting two RGB frames from each other,
         - identifying ON and OFF events as pixels with values greater than theta and values
           less than -theta, respectively
         - emulating an event image by marking ON and OFF events with red and blue in a white frame

        Parameters
        ----------
        frame: numpy.ndarray
            Current RGB image array.
        previous_frame: numpy.ndarray
            Previous RGB image array.
        theta: int
            Threshold value. Smaller values lead to more noisy results.
        
        Returns
        -------
        event_frame: numpy.ndarray
            Estimated event image array.
        '''
        ## Frames must be cast to signed ints before computing diffs
        ## Otherwise, negative numbers wrap around to 255...
        diff_frame = frame.astype(int) - previous_frame.astype(int)
        theta_frame = np.full((diff_frame.shape[0], diff_frame.shape[1], 3), theta, dtype='uint8')

        ## Find indices of pixels for which R,G,B are all > theta:
        bools = (diff_frame - theta_frame) > 0.
        # Note: If RGB are all True, the sum for a pixel would be 3:
        on_indices = np.sum(bools, 2) >= 1.

        ## Find indices of pixels for which R,G,B are all < theta:
        bools = (diff_frame + theta_frame) < 0.
        # Note: If RGB are all True, the sum for a pixel would be 3:
        off_indices = np.sum(bools, 2) >= 1.

        event_frame = np.full((frame.shape[0], frame.shape[1], 3), 255., dtype='uint8')

        event_frame[on_indices] = [255., 0., 0.]
        if record_off_events:
            event_frame[off_indices] = [0., 0., 255.]

        return event_frame
